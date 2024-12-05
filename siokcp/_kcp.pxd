# cython: language_level=3
# cython: cdivision=True
from libc.stdint cimport uint32_t


cdef extern from "ikcp.h" nogil:
    ctypedef void (*writelog_cb_t)(const char *log, ikcpcb *kcp, void *user) except* with gil
    ctypedef int (*output_cb_t)(const char *buf, int len, ikcpcb *kcp, void *user) except* with gil
    ctypedef struct ikcpcb:
        uint32_t conv
        uint32_t mtu
        uint32_t mss
        uint32_t state
        uint32_t snd_una
        uint32_t snd_nxt
        uint32_t rcv_nxt
        uint32_t ts_recent
        uint32_t ts_lastack
        uint32_t ssthresh
        uint32_t rx_rttval
        uint32_t rx_srtt
        uint32_t rx_rto
        uint32_t rx_minrto
        uint32_t snd_wnd
        uint32_t rcv_wnd
        uint32_t rmt_wnd
        uint32_t cwnd
        uint32_t probe
        uint32_t current
        uint32_t interval
        uint32_t ts_flush
        uint32_t xmit
        uint32_t nrcv_buf
        uint32_t nsnd_buf
        uint32_t nrcv_que
        uint32_t nsnd_que
        uint32_t nodelay
        uint32_t updated
        uint32_t ts_probe
        uint32_t probe_wait
        uint32_t dead_link
        uint32_t incr
        int fastresend
        int fastlimit
        int nocwnd
        int stream
        int logmask

        output_cb_t output
        writelog_cb_t writelog
    ikcpcb* ikcp_create(uint32_t conv, void *user)

    # release kcp control object
    void ikcp_release(ikcpcb *kcp)

    # set output callback, which will be invoked by kcp

    void ikcp_setoutput(ikcpcb *kcp, output_cb_t output)

    # user/upper level recv: returns size, returns below zero for EAGAIN
    int ikcp_recv(ikcpcb *kcp, char *buffer, int len)

    # user/upper level send, returns below zero for error
    int ikcp_send(ikcpcb *kcp, const char *buffer, int len)

    # update state (call it repeatedly, every 10ms-100ms), or you can ask
    # ikcp_check when to call it again (without ikcp_input/_send calling).
    # 'current' - current timestamp in millisec.
    void ikcp_update(ikcpcb *kcp, uint32_t current)

    # Determine when should you invoke ikcp_update:
    # returns when you should invoke ikcp_update in millisec, if there
    # is no ikcp_input/_send calling. you can call ikcp_update in that
    # time, instead of call update repeatly.
    # Important to reduce unnacessary ikcp_update invoking. use it to
    # schedule ikcp_update (eg. implementing an epoll-like mechanism,
    # or optimize ikcp_update when handling massive kcp connections)
    uint32_t ikcp_check(const ikcpcb *kcp, uint32_t current)

    # when you received a low level packet (eg. UDP packet), call it
    int ikcp_input(ikcpcb *kcp, const char *data, long size)

    # flush pending data
    void ikcp_flush(ikcpcb *kcp)

    # check the size of next message in the recv queue
    int ikcp_peeksize(const ikcpcb *kcp)

    # change MTU size, default is 1400
    int ikcp_setmtu(ikcpcb *kcp, int mtu)

    # set maximum window size: sndwnd=32, rcvwnd=32 by default
    int ikcp_wndsize(ikcpcb *kcp, int sndwnd, int rcvwnd)

    # get how many packet is waiting to be sent
    int ikcp_waitsnd(const ikcpcb *kcp)

    # fastest: ikcp_nodelay(kcp, 1, 20, 2, 1)
    # nodelay: 0:disable(default), 1:enable
    # interval: internal update timer interval in millisec, default is 100ms
    # resend: 0:disable fast resend(default), 1:enable fast resend
    # nc: 0:normal congestion control(default), 1:disable congestion control
    int ikcp_nodelay(ikcpcb *kcp, int nodelay, int interval, int resend, int nc)


    void ikcp_log(ikcpcb *kcp, int mask, const char *fmt, ...)

    # setup allocator
    void ikcp_allocator(void* (*new_malloc)(size_t), void (*new_free)(void*))

    # read conv
    uint32_t ikcp_getconv(const void *ptr)

    int IKCP_LOG_OUTPUT_C         "IKCP_LOG_OUTPUT"
    int IKCP_LOG_INPUT_C         "IKCP_LOG_INPUT"
    int IKCP_LOG_SEND_C           "IKCP_LOG_SEND"
    int IKCP_LOG_RECV_C           "IKCP_LOG_RECV"
    int IKCP_LOG_IN_DATA_C        "IKCP_LOG_IN_DATA"
    int IKCP_LOG_IN_ACK_C         "IKCP_LOG_IN_ACK"
    int IKCP_LOG_IN_PROBE_C       "IKCP_LOG_IN_PROBE"
    int IKCP_LOG_IN_WINS_C        "IKCP_LOG_IN_WINS"
    int IKCP_LOG_OUT_DATA_C       "IKCP_LOG_OUT_DATA"
    int IKCP_LOG_OUT_ACK_C        "IKCP_LOG_OUT_ACK"
    int IKCP_LOG_OUT_PROBE_C      "IKCP_LOG_OUT_PROBE"
    int IKCP_LOG_OUT_WINS_C       "IKCP_LOG_OUT_WINS"
