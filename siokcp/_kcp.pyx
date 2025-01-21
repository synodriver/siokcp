# cython: language_level=3
# cython: cdivision=True
cimport cython
from cpython.bytes cimport PyBytes_AS_STRING, PyBytes_FromStringAndSize
from cpython.mem cimport PyMem_RawFree, PyMem_RawMalloc
from cpython.pycapsule cimport PyCapsule_New
from cpython.unicode cimport PyUnicode_AsUTF8, PyUnicode_FromString
from libc.stdint cimport uint8_t, uint32_t

from siokcp cimport kcp

IKCP_LOG_OUTPUT	      =          kcp.IKCP_LOG_OUTPUT_C
IKCP_LOG_INPUT	      =          kcp.IKCP_LOG_INPUT_C
IKCP_LOG_SEND	      =          kcp.IKCP_LOG_SEND_C
IKCP_LOG_RECV	      =          kcp.IKCP_LOG_RECV_C
IKCP_LOG_IN_DATA      =          kcp.IKCP_LOG_IN_DATA_C
IKCP_LOG_IN_ACK	      =          kcp.IKCP_LOG_IN_ACK_C
IKCP_LOG_IN_PROBE     =           kcp.IKCP_LOG_IN_PROBE_C
IKCP_LOG_IN_WINS      =          kcp.IKCP_LOG_IN_WINS_C
IKCP_LOG_OUT_DATA     =           kcp.IKCP_LOG_OUT_DATA_C
IKCP_LOG_OUT_ACK      =          kcp.IKCP_LOG_OUT_ACK_C
IKCP_LOG_OUT_PROBE    =            kcp.IKCP_LOG_OUT_PROBE_C
IKCP_LOG_OUT_WINS     =           kcp.IKCP_LOG_OUT_WINS_C



cdef int kcp_output_cb(const char *buf, int len,  kcp.ikcpcb *kcp, void *user) with gil:
    cdef bytes data = PyBytes_FromStringAndSize(buf, len)
    cdef KCPConnection con = <KCPConnection>user
    return con.send_cb(data)

cdef void kcp_writelog_cb(const char *log, kcp.ikcpcb *kcp, void *user) with gil:
    cdef str data = PyUnicode_FromString(log)
    cdef KCPConnection con = <KCPConnection> user
    con.log_cb(data)

@cython.no_gc
@cython.freelist(8)
@cython.final
cdef class KCPConnection:
    cdef:
        kcp.ikcpcb *_kcp
        public object send_cb
        object log_cb


    def __cinit__(self, uint32_t conv, object send_cb, object log_cb):
        self.send_cb = send_cb
        self.log_cb = log_cb
        self._kcp = kcp.ikcp_create(conv, <void *>self)
        if self._kcp == NULL:
            raise MemoryError
        kcp.ikcp_setoutput(self._kcp, kcp_output_cb)
        self._kcp.writelog = kcp_writelog_cb

    def __dealloc__(self):
        kcp.ikcp_release(self._kcp)
        self._kcp = NULL

    @property
    def conv(self):
        return self._kcp.conv

    @conv.setter
    def conv(self, uint32_t value):
        self._kcp.conv = value

    @property
    def mtu(self):
        return self._kcp.mtu

    @mtu.setter
    def mtu(self, uint32_t value):
        self._kcp.mtu = value

    @property
    def mss(self):
        return self._kcp.mss

    @mss.setter
    def mss(self, uint32_t value):
        self._kcp.mss = value

    @property
    def state(self):
        return <int>self._kcp.state # although it's uint32_t, we treat it as int

    @state.setter
    def state(self, int value):
        self._kcp.state = <uint32_t>value

    @property
    def snd_una(self):
        return self._kcp.snd_una

    @snd_una.setter
    def snd_una(self, uint32_t value):
        self._kcp.snd_una = value

    @property
    def snd_nxt(self):
        return self._kcp.snd_nxt

    @snd_nxt.setter
    def snd_nxt(self, uint32_t value):
        self._kcp.snd_nxt = value

    @property
    def rcv_nxt(self):
        return self._kcp.rcv_nxt

    @rcv_nxt.setter
    def rcv_nxt(self, uint32_t value):
        self._kcp.rcv_nxt = value

    @property
    def ts_recent(self):
        return self._kcp.ts_recent

    @ts_recent.setter
    def ts_recent(self, uint32_t value):
        self._kcp.ts_recent = value

    @property
    def ts_lastack(self):
        return self._kcp.ts_lastack

    @ts_lastack.setter
    def ts_lastack(self, uint32_t value):
        self._kcp.ts_lastack = value

    @property
    def ssthresh(self):
        return self._kcp.ssthresh

    @ssthresh.setter
    def ssthresh(self, uint32_t value):
        self._kcp.ssthresh = value

    @property
    def rx_rttval(self):
        return self._kcp.rx_rttval

    @rx_rttval.setter
    def rx_rttval(self, uint32_t value):
        self._kcp.rx_rttval = value

    @property
    def rx_srtt(self):
        return self._kcp.rx_srtt

    @rx_srtt.setter
    def rx_srtt(self, uint32_t value):
        self._kcp.rx_srtt = value

    @property
    def rx_rto(self):
        return self._kcp.rx_rto

    @rx_rto.setter
    def rx_rto(self, uint32_t value):
        self._kcp.rx_rto = value

    @property
    def rx_minrto(self):
        return self._kcp.rx_minrto

    @rx_minrto.setter
    def rx_minrto(self, uint32_t value):
        self._kcp.rx_minrto = value

    @property
    def snd_wnd(self):
        return self._kcp.snd_wnd

    @snd_wnd.setter
    def snd_wnd(self, uint32_t value):
        self._kcp.snd_wnd = value

    @property
    def rcv_wnd(self):
        return self._kcp.rcv_wnd

    @rcv_wnd.setter
    def rcv_wnd(self, uint32_t value):
        self._kcp.rcv_wnd = value

    @property
    def rmt_wnd(self):
        return self._kcp.rmt_wnd

    @rmt_wnd.setter
    def rmt_wnd(self, uint32_t value):
        self._kcp.rmt_wnd = value

    @property
    def cwnd(self):
        return self._kcp.cwnd

    @cwnd.setter
    def cwnd(self, uint32_t value):
        self._kcp.cwnd = value

    @property
    def probe(self):
        return self._kcp.probe

    @probe.setter
    def probe(self, uint32_t value):
        self._kcp.probe = value

    @property
    def current(self):
        return self._kcp.current

    @current.setter
    def current(self, uint32_t value):
        self._kcp.current = value

    @property
    def interval(self):
        return self._kcp.interval

    @interval.setter
    def interval(self, uint32_t value):
        self._kcp.interval = value

    @property
    def ts_flush(self):
        return self._kcp.ts_flush

    @ts_flush.setter
    def ts_flush(self, uint32_t value):
        self._kcp.ts_flush = value

    @property
    def xmit(self):
        return self._kcp.xmit

    @xmit.setter
    def xmit(self, uint32_t value):
        self._kcp.xmit = value

    @property
    def nrcv_buf(self):
        return self._kcp.nrcv_buf

    @nrcv_buf.setter
    def nrcv_buf(self, uint32_t value):
        self._kcp.nrcv_buf = value

    @property
    def nsnd_buf(self):
        return self._kcp.nsnd_buf

    @nsnd_buf.setter
    def nsnd_buf(self, uint32_t value):
        self._kcp.nsnd_buf = value

    @property
    def nrcv_que(self):
        return self._kcp.nrcv_que

    @nrcv_que.setter
    def nrcv_que(self, uint32_t value):
        self._kcp.nrcv_que = value

    @property
    def nsnd_que(self):
        return self._kcp.nsnd_que

    @nsnd_que.setter
    def nsnd_que(self, uint32_t value):
        self._kcp.nsnd_que = value

    @property
    def nodelay_(self):
        return self._kcp.nodelay

    @nodelay_.setter
    def nodelay_(self, uint32_t value):
        self._kcp.nodelay = value

    @property
    def updated(self):
        return self._kcp.updated

    @updated.setter
    def updated(self, uint32_t value):
        self._kcp.updated = value

    @property
    def ts_probe(self):
        return self._kcp.ts_probe

    @ts_probe.setter
    def ts_probe(self, uint32_t value):
        self._kcp.ts_probe = value

    @property
    def probe_wait(self):
        return self._kcp.probe_wait

    @probe_wait.setter
    def probe_wait(self, uint32_t value):
        self._kcp.probe_wait = value

    @property
    def dead_link(self):
        return self._kcp.dead_link

    @dead_link.setter
    def dead_link(self, uint32_t value):
        self._kcp.dead_link = value

    @property
    def incr(self):
        return self._kcp.incr

    @incr.setter
    def incr(self, uint32_t value):
        self._kcp.incr = value

    @property
    def fastresend(self):
        return self._kcp.fastresend

    @fastresend.setter
    def fastresend(self, int value):
        self._kcp.fastresend = value

    @property
    def fastlimit(self):
        return self._kcp.fastlimit

    @fastlimit.setter
    def fastlimit(self, int value):
        self._kcp.fastlimit = value

    @property
    def nocwnd(self):
        return self._kcp.nocwnd

    @nocwnd.setter
    def nocwnd(self, int value):
        self._kcp.nocwnd = value

    @property
    def stream(self):
        return self._kcp.stream

    @stream.setter
    def stream(self, int value):
        self._kcp.stream = value

    @property
    def logmask(self):
        return self._kcp.logmask

    @logmask.setter
    def logmask(self, int value):
        self._kcp.logmask = value

    cpdef inline bytes next_event(self):
        """
        Return None for EAGAIN
        :return: next packet
        """
        cdef int hr
        cdef int size = kcp.ikcp_peeksize(self._kcp)
        if size < 0:
            return None
        cdef bytes out = PyBytes_FromStringAndSize(NULL, <Py_ssize_t>size)
        cdef const char *out_ptr = PyBytes_AS_STRING(out)
        with nogil:
            hr = kcp.ikcp_recv(self._kcp, <char*>out_ptr, size)
        if hr < 0:
            return None
        return out

    cpdef inline int next_event_into(self, uint8_t[::1] buffer):
        """
        you may need to call this multiple times to get all data, until it returns 0
        :return: 
        """
        cdef int hr
        with nogil:
            hr = kcp.ikcp_recv(self._kcp, <char *>&buffer[0], <int> buffer.shape[0])
        return hr

    cpdef inline int send(self, const uint8_t[::1] data) except -1:
        cdef int ret
        with nogil:
            ret = kcp.ikcp_send(self._kcp, <const char*>&data[0], <int>data.shape[0])
        if ret < 0:
            raise ValueError(f"kcp send error: {ret}") # todo 自定义异常类型
        return ret

    cpdef inline update(self, uint32_t current):
        with nogil:
            kcp.ikcp_update(self._kcp, current)

    cpdef inline uint32_t check(self, uint32_t current):
        cdef uint32_t ret
        with nogil:
            ret = kcp.ikcp_check(self._kcp, current)
        return ret

    cpdef inline int receive_data(self, const uint8_t[::1] data):
        cdef int ret
        with nogil:
            ret = kcp.ikcp_input(self._kcp, <char*>&data[0], <long>data.shape[0])
        return ret

    cpdef inline flush(self):
        with nogil:
            kcp.ikcp_flush(self._kcp)

    cpdef inline int peeksize(self):
        cdef int ret
        with nogil:
            ret = kcp.ikcp_peeksize(self._kcp)
        return ret

    cpdef inline int setmtu(self, int mtu):
        cdef int ret
        with nogil:
            ret = kcp.ikcp_setmtu(self._kcp, mtu)
        return ret

    cpdef inline int wndsize(self, int sndwnd, int rcvwnd):
        cdef int ret
        with nogil:
            ret = kcp.ikcp_wndsize(self._kcp, sndwnd, rcvwnd)
        return ret

    cpdef inline int waitsnd(self):
        cdef int ret
        with nogil:
            ret = kcp.ikcp_waitsnd(self._kcp)
        return ret

    cpdef inline int nodelay(self, int nodelay, int interval, int resend, int nc):
        cdef int ret
        with nogil:
            ret = kcp.ikcp_nodelay(self._kcp, nodelay, interval, resend, nc)
        return ret

    cpdef inline log(self, int mask, str data):
        cdef const char* data_ptr = PyUnicode_AsUTF8(data)
        with nogil:
            kcp.ikcp_log(self._kcp, mask, data_ptr)

    cpdef inline object get_ptr(self):
        return PyCapsule_New(self._kcp, NULL, NULL) # expose the c ptr

kcp.ikcp_allocator(PyMem_RawMalloc, PyMem_RawFree)

cpdef inline uint32_t getconv(const uint8_t[::1] data):
    """Get conversation id from raw data
    :param data: raw data read from socket, usually at the beginning of a session
    :return: conversation id, aka conv
    """
    cdef uint32_t ret
    with nogil:
        ret = kcp.ikcp_getconv(&data[0])
    return ret

ikcp_create = PyCapsule_New(<void*>kcp.ikcp_create, "siokcp._kcp.ikcp_create", NULL)
ikcp_release = PyCapsule_New(<void*>kcp.ikcp_release, "siokcp._kcp.ikcp_release", NULL)
ikcp_setoutput = PyCapsule_New(<void*>kcp.ikcp_setoutput, "siokcp._kcp.ikcp_setoutput", NULL)
ikcp_recv = PyCapsule_New(<void*>kcp.ikcp_recv, "siokcp._kcp.ikcp_recv", NULL)
ikcp_send = PyCapsule_New(<void*>kcp.ikcp_send, "siokcp._kcp.ikcp_send", NULL)
ikcp_update = PyCapsule_New(<void*>kcp.ikcp_update, "siokcp._kcp.ikcp_update", NULL)
ikcp_check = PyCapsule_New(<void*>kcp.ikcp_check, "siokcp._kcp.ikcp_check", NULL)
ikcp_input = PyCapsule_New(<void*>kcp.ikcp_input, "siokcp._kcp.ikcp_input", NULL)
ikcp_flush = PyCapsule_New(<void*>kcp.ikcp_flush, "siokcp._kcp.ikcp_flush", NULL)
ikcp_peeksize = PyCapsule_New(<void*>kcp.ikcp_peeksize, "siokcp._kcp.ikcp_peeksize", NULL)
ikcp_setmtu = PyCapsule_New(<void*>kcp.ikcp_setmtu, "siokcp.siokcp._kcp.ikcp_setmtu", NULL)
ikcp_wndsize = PyCapsule_New(<void*>kcp.ikcp_wndsize, "siokcp._kcp.ikcp_wndsize", NULL)
ikcp_waitsnd = PyCapsule_New(<void*>kcp.ikcp_waitsnd, "siokcp._kcp.ikcp_waitsnd", NULL)
ikcp_nodelay = PyCapsule_New(<void*>kcp.ikcp_nodelay, "siokcp._kcp.ikcp_nodelay", NULL)
ikcp_log = PyCapsule_New(<void*>kcp.ikcp_log, "siokcp._kcp.ikcp_log", NULL)
ikcp_allocator = PyCapsule_New(<void*>kcp.ikcp_allocator, "siokcp._kcp.ikcp_allocator", NULL)
ikcp_getconv = PyCapsule_New(<void*>kcp.ikcp_getconv, "siokcp._kcp.ikcp_getconv", NULL)
