from unittest import TestCase
from walkoff.sse import SimpleFilteredSseStream, SseEvent
from tests.util.mock_objects import MockRedisCacheAdapter
import gevent
from gevent.monkey import patch_all

class TestSimpleFilteredSseStream(TestCase):
    @classmethod
    def setUpClass(cls):
        patch_all()

    def setUp(self):
        self.cache = MockRedisCacheAdapter()
        self.channel = 'channel1'
        self.stream = SimpleFilteredSseStream(self.channel, self.cache)

    def tearDown(self):
        self.cache.clear()

    def test_init(self):
        self.assertEqual(self.stream.channel, self.channel)
        self.assertEqual(self.stream.cache, self.cache)

    def test_create_channel_name(self):
        self.assertEqual(self.stream.create_channel_name('a'), '{}.a'.format(self.channel))
        self.assertEqual(self.stream.create_channel_name(14), '{}.14'.format(self.channel))

    def assert_header_in_response(self, response, header, value):
        header_tuple = next((header_ for header_ in response.headers if header_[0] == header), None)
        self.assertIsNotNone(header_tuple)
        self.assertEqual(header_tuple[1], value)

    def test_stream_default_headers(self):
        resp = self.stream.stream(subchannel='a')
        self.assert_header_in_response(resp, 'Connection', 'keep-alive')
        self.assert_header_in_response(resp, 'Cache-Control', 'no-cache')
        self.assert_header_in_response(resp, 'Content-Type', 'text/event-stream; charset=utf-8')

    def test_stream_custom_headers(self):
        resp = self.stream.stream(subchannel='a', headers={'x-custom': 'yes', 'Cache-Control': 'no-store'})
        self.assert_header_in_response(resp, 'Connection', 'keep-alive')
        self.assert_header_in_response(resp, 'Cache-Control', 'no-store')
        self.assert_header_in_response(resp, 'Content-Type', 'text/event-stream; charset=utf-8')
        self.assert_header_in_response(resp, 'x-custom', 'yes')

    def test_send(self):

        @self.stream.push('event1')
        def pusher(a, ev, sub):
            return {'a': a}, sub, ev

        subs = ('a', 'b')

        result = {'a': [], 'b': []}

        def listen(sub):
            for event in self.stream.send(subchannel=sub):
                result[sub].append(event)

        base_args = [('event1', 1), ('event2', 2)]
        args = {sub: [(event, data + i) for (event, data) in base_args] for i, sub in enumerate(subs)}

        def publish(sub):
            for event, data in args[sub]:
                pusher(data, event, sub)
            self.stream.unsubscribe(sub)

        sses = {sub: [SseEvent(event, {'a': arg}) for event, arg in args[sub]] for sub in subs}
        formatted_sses = {sub: [sse.format(i + 1) for i, sse in enumerate(sse_vals)] for sub, sse_vals in sses.items()}

        listen_threads = [gevent.spawn(listen, sub) for sub in subs]
        publish_threads = [gevent.spawn(publish, sub) for sub in subs]
        gevent.joinall(listen_threads, timeout=2)
        gevent.joinall(publish_threads, timeout=2)
        for sub in subs:
            self.assertListEqual(result[sub], formatted_sses[sub])

    '''
    def test_send_with_retry(self):

        @self.stream.push('event1')
        def pusher(a, ev):
            return {'a': a}, ev

        result = []

        def listen():
            for event in self.stream.send(retry=50):
                result.append(event)

        args = [('event1', 1), ('event2', 2)]
        sses = [SseEvent(event, {'a': arg}) for event, arg in args]
        formatted_sses = [sse.format(i+1, retry=50) for i, sse in enumerate(sses)]

        def publish():
            for event, data in args:
                pusher(data, event)
            self.stream.unsubscribe()

        thread = gevent.spawn(listen)
        thread2 = gevent.spawn(publish)
        thread.start()
        thread2.start()
        thread.join(timeout=2)
        thread2.join(timeout=2)
        self.assertListEqual(result, formatted_sses)

    def test_stream_with_data(self):
        @self.stream.push('event1')
        def pusher(a, ev):
            return {'a': a}, ev

        result = []

        def listen():
            response = self.stream.stream()
            for event in response.response:
                result.append(event)

        args = [('event1', 1), ('event2', 2)]
        sses = [SseEvent(event, {'a': arg}) for event, arg in args]
        formatted_sses = [sse.format(i+1) for i, sse in enumerate(sses)]

        def publish():
            for event, data in args:
                pusher(data, event)
            self.stream.unsubscribe()

        thread = gevent.spawn(listen)
        thread2 = gevent.spawn(publish)
        thread.start()
        thread2.start()
        thread.join(timeout=2)
        thread2.join(timeout=2)
        self.assertListEqual(result, formatted_sses)

    def test_stream_with_data_with_retry(self):
        @self.stream.push('event1')
        def pusher(a, ev):
            return {'a': a}, ev

        result = []

        def listen():
            response = self.stream.stream(retry=100)
            for event in response.response:
                result.append(event)

        args = [('event1', 1), ('event2', 2)]
        sses = [SseEvent(event, {'a': arg}) for event, arg in args]
        formatted_sses = [sse.format(i+1, retry=100) for i, sse in enumerate(sses)]

        def publish():
            for event, data in args:
                pusher(data, event)
            self.stream.unsubscribe()

        thread = gevent.spawn(listen)
        thread2 = gevent.spawn(publish)
        thread.start()
        thread2.start()
        thread.join(timeout=2)
        thread2.join(timeout=2)
        self.assertListEqual(result, formatted_sses)
    '''
