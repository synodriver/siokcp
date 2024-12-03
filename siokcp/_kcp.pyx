# cython: language_level=3
# cython: cdivision=True
cimport cython
from cpython.bytes cimport PyBytes_AS_STRING, PyBytes_FromStringAndSize
from cpython.mem cimport PyMem_RawFree, PyMem_RawMalloc
from cpython.unicode cimport PyUnicode_AsUTF8, PyUnicode_FromString
from libc.stdint cimport uint8_t, uint32_t

from siokcp._kcp cimport (ikcp_check, ikcp_create, ikcp_flush, ikcp_input,
                          ikcp_peeksize, ikcp_recv, ikcp_release, ikcp_send,
                          ikcp_setoutput, ikcp_update, ikcpcb)


cdef int kcp_output_cb(const char *buf, int len,  ikcpcb *kcp, void *user) with gil:
    cdef bytes data = PyBytes_FromStringAndSize(buf, len)
    cdef KCPConnection con = <KCPConnection>user
    return con.send_cb(data)

cdef void kcp_writelog_cb(const char *log, ikcpcb *kcp, void *user) with gil:
    cdef str data = PyUnicode_FromString(log)
    cdef KCPConnection con = <KCPConnection> user
    con.log_cb(data)

@cython.no_gc
@cython.freelist(8)
@cython.final
cdef class KCPConnection:
    cdef:
        ikcpcb *_kcp
        object send_cb
        object log_cb


    def __cinit__(self, uint32_t conv, object send_cb, object log_cb):
        self.send_cb = send_cb
        self.log_cb = log_cb
        self._kcp = ikcp_create(conv, <void *>self)
        if self._kcp == NULL:
            raise MemoryError
        ikcp_setoutput(self._kcp, kcp_output_cb)
        self._kcp.writelog = kcp_writelog_cb

    def __dealloc__(self):
        ikcp_release(self._kcp)
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
        return self._kcp.state

    @state.setter
    def state(self, uint32_t value):
        self._kcp.state = value

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
        cdef int size = ikcp_peeksize(self._kcp)
        if size < 0:
            return None
        cdef bytes out = PyBytes_FromStringAndSize(NULL, <Py_ssize_t>size)
        cdef const char *out_ptr = PyBytes_AS_STRING(out)
        with nogil:
            hr = ikcp_recv(self._kcp, <char*>out_ptr, size)
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
            hr = ikcp_recv(self._kcp, <char *>&buffer[0], <int> buffer.shape[0])
        return hr

    cpdef inline int send(self, const uint8_t[::1] data) except -1:
        cdef int ret
        with nogil:
            ret = ikcp_send(self._kcp, <const char*>&data[0], <int>data.shape[0])
        if ret < 0:
            raise ValueError(f"kcp send error: {ret}") # todo 自定义异常类型
        return ret

    cpdef inline update(self, uint32_t current):
        with nogil:
            ikcp_update(self._kcp, current)

    cpdef inline uint32_t check(self, uint32_t current):
        cdef uint32_t ret
        with nogil:
            ret = ikcp_check(self._kcp, current)
        return ret

    cpdef inline int receive_data(self, const uint8_t[::1] data):
        cdef int ret
        with nogil:
            ret = ikcp_input(self._kcp, <char*>&data[0], <long>data.shape[0])
        return ret

    cpdef inline flush(self):
        with nogil:
            ikcp_flush(self._kcp)

    cpdef inline int peeksize(self):
        cdef int ret
        with nogil:
            ret = ikcp_peeksize(self._kcp)
        return ret

    cpdef inline int setmtu(self, int mtu):
        cdef int ret
        with nogil:
            ret = ikcp_setmtu(self._kcp, mtu)
        return ret

    cpdef inline int wndsize(self, int sndwnd, int rcvwnd):
        cdef int ret
        with nogil:
            ret = ikcp_wndsize(self._kcp, sndwnd, rcvwnd)
        return ret

    cpdef inline int waitsnd(self):
        cdef int ret
        with nogil:
            ret = ikcp_waitsnd(self._kcp)
        return ret

    cpdef inline int nodelay(self, int nodelay, int interval, int resend, int nc):
        cdef int ret
        with nogil:
            ret = ikcp_nodelay(self._kcp, nodelay, interval, resend, nc)
        return ret

    cpdef inline log(self, int mask, str data):
        cdef const char* data_ptr = PyUnicode_AsUTF8(data)
        with nogil:
            ikcp_log(self._kcp, mask, data_ptr)


ikcp_allocator(PyMem_RawMalloc, PyMem_RawFree)

cpdef inline uint32_t getconv(const uint8_t[::1] data):
    """Get conversation id from raw data
    :param data: raw data read from socket, usually at the beginning of a session
    :return: conversation id, aka conv
    """
    cdef uint32_t ret
    with nogil:
        ret = ikcp_getconv(&data[0])
    return ret