# -*- coding: utf-8 -*-
from unittest import TestCase
import ctypes


from siokcp import KCPConnection
from functools import partial

PyCapsule_GetPointer = ctypes.pythonapi.PyCapsule_GetPointer

PyCapsule_GetPointer.argtypes = [ctypes.py_object, ctypes.c_char_p]
PyCapsule_GetPointer.restype = ctypes.c_void_p

class Kcp(ctypes.Structure):
    _fields_ = [("conv", ctypes.c_uint32),("mtu", ctypes.c_uint32)]

class TestCtypes(TestCase):
    def setUp(self):
        ...

    def tearDown(self):
        ...

    def test_kcp_object(self):
        for conv in range(10):
            con = KCPConnection(conv, partial(print, "send"), partial(print, "log"))
            capsule = con.get_ptr()
            intptr = PyCapsule_GetPointer(ctypes.py_object(capsule), None)
            voidptr = ctypes.cast(intptr, ctypes.c_void_p)
            kcp_p = ctypes.cast(voidptr, ctypes.POINTER(Kcp))
            ret = kcp_p[0].conv
            ret2= kcp_p[0].mtu
            self.assertEqual(conv, ret)
            self.assertEqual(1400, ret2)

    def test_kcp_func(self):
        from siokcp._kcp import ikcp_create, ikcp_release
        intptr  = PyCapsule_GetPointer(ctypes.py_object(ikcp_create), b"siokcp._kcp.ikcp_create")
        voidptr = ctypes.cast(intptr, ctypes.c_void_p)
        ikcp_create_t = ctypes.CFUNCTYPE(ctypes.POINTER(Kcp), ctypes.c_uint32, ctypes.c_void_p)
        ikcp_create = ctypes.cast(voidptr, ikcp_create_t)

        intptr = PyCapsule_GetPointer(ctypes.py_object(ikcp_release), b"siokcp._kcp.ikcp_release")
        voidptr = ctypes.cast(intptr, ctypes.c_void_p)
        ikcp_release_t = ctypes.CFUNCTYPE(None, ctypes.POINTER(Kcp))
        ikcp_release = ctypes.cast(voidptr, ikcp_release_t)

        for conv in range(100):
            kcp = ikcp_create(conv, None)
            self.assertEqual(kcp[0].conv, conv)
            self.assertEqual(kcp[0].mtu, 1400)
            ikcp_release(kcp)