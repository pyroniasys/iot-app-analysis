'''Autogenerated by xml_generate script, do not edit!'''
from OpenGL import platform as _p, arrays
# Code generation uses this
from OpenGL.raw.GL import _types as _cs
# End users want this...
from OpenGL.raw.GL._types import *
from OpenGL.raw.GL import _errors
from OpenGL.constant import Constant as _C

import ctypes
_EXTENSION_NAME = 'GL_KHR_debug'
def _f( function ):
    return _p.createFunction( function,_p.PLATFORM.GL,'GL_KHR_debug',error_checker=_errors._error_checker)
GL_BUFFER=_C('GL_BUFFER',0x82E0)
GL_BUFFER_KHR=_C('GL_BUFFER_KHR',0x82E0)
GL_CONTEXT_FLAG_DEBUG_BIT=_C('GL_CONTEXT_FLAG_DEBUG_BIT',0x00000002)
GL_CONTEXT_FLAG_DEBUG_BIT_KHR=_C('GL_CONTEXT_FLAG_DEBUG_BIT_KHR',0x00000002)
GL_DEBUG_CALLBACK_FUNCTION=_C('GL_DEBUG_CALLBACK_FUNCTION',0x8244)
GL_DEBUG_CALLBACK_FUNCTION_KHR=_C('GL_DEBUG_CALLBACK_FUNCTION_KHR',0x8244)
GL_DEBUG_CALLBACK_USER_PARAM=_C('GL_DEBUG_CALLBACK_USER_PARAM',0x8245)
GL_DEBUG_CALLBACK_USER_PARAM_KHR=_C('GL_DEBUG_CALLBACK_USER_PARAM_KHR',0x8245)
GL_DEBUG_GROUP_STACK_DEPTH=_C('GL_DEBUG_GROUP_STACK_DEPTH',0x826D)
GL_DEBUG_GROUP_STACK_DEPTH_KHR=_C('GL_DEBUG_GROUP_STACK_DEPTH_KHR',0x826D)
GL_DEBUG_LOGGED_MESSAGES=_C('GL_DEBUG_LOGGED_MESSAGES',0x9145)
GL_DEBUG_LOGGED_MESSAGES_KHR=_C('GL_DEBUG_LOGGED_MESSAGES_KHR',0x9145)
GL_DEBUG_NEXT_LOGGED_MESSAGE_LENGTH=_C('GL_DEBUG_NEXT_LOGGED_MESSAGE_LENGTH',0x8243)
GL_DEBUG_NEXT_LOGGED_MESSAGE_LENGTH_KHR=_C('GL_DEBUG_NEXT_LOGGED_MESSAGE_LENGTH_KHR',0x8243)
GL_DEBUG_OUTPUT=_C('GL_DEBUG_OUTPUT',0x92E0)
GL_DEBUG_OUTPUT_KHR=_C('GL_DEBUG_OUTPUT_KHR',0x92E0)
GL_DEBUG_OUTPUT_SYNCHRONOUS=_C('GL_DEBUG_OUTPUT_SYNCHRONOUS',0x8242)
GL_DEBUG_OUTPUT_SYNCHRONOUS_KHR=_C('GL_DEBUG_OUTPUT_SYNCHRONOUS_KHR',0x8242)
GL_DEBUG_SEVERITY_HIGH=_C('GL_DEBUG_SEVERITY_HIGH',0x9146)
GL_DEBUG_SEVERITY_HIGH_KHR=_C('GL_DEBUG_SEVERITY_HIGH_KHR',0x9146)
GL_DEBUG_SEVERITY_LOW=_C('GL_DEBUG_SEVERITY_LOW',0x9148)
GL_DEBUG_SEVERITY_LOW_KHR=_C('GL_DEBUG_SEVERITY_LOW_KHR',0x9148)
GL_DEBUG_SEVERITY_MEDIUM=_C('GL_DEBUG_SEVERITY_MEDIUM',0x9147)
GL_DEBUG_SEVERITY_MEDIUM_KHR=_C('GL_DEBUG_SEVERITY_MEDIUM_KHR',0x9147)
GL_DEBUG_SEVERITY_NOTIFICATION=_C('GL_DEBUG_SEVERITY_NOTIFICATION',0x826B)
GL_DEBUG_SEVERITY_NOTIFICATION_KHR=_C('GL_DEBUG_SEVERITY_NOTIFICATION_KHR',0x826B)
GL_DEBUG_SOURCE_API=_C('GL_DEBUG_SOURCE_API',0x8246)
GL_DEBUG_SOURCE_API_KHR=_C('GL_DEBUG_SOURCE_API_KHR',0x8246)
GL_DEBUG_SOURCE_APPLICATION=_C('GL_DEBUG_SOURCE_APPLICATION',0x824A)
GL_DEBUG_SOURCE_APPLICATION_KHR=_C('GL_DEBUG_SOURCE_APPLICATION_KHR',0x824A)
GL_DEBUG_SOURCE_OTHER=_C('GL_DEBUG_SOURCE_OTHER',0x824B)
GL_DEBUG_SOURCE_OTHER_KHR=_C('GL_DEBUG_SOURCE_OTHER_KHR',0x824B)
GL_DEBUG_SOURCE_SHADER_COMPILER=_C('GL_DEBUG_SOURCE_SHADER_COMPILER',0x8248)
GL_DEBUG_SOURCE_SHADER_COMPILER_KHR=_C('GL_DEBUG_SOURCE_SHADER_COMPILER_KHR',0x8248)
GL_DEBUG_SOURCE_THIRD_PARTY=_C('GL_DEBUG_SOURCE_THIRD_PARTY',0x8249)
GL_DEBUG_SOURCE_THIRD_PARTY_KHR=_C('GL_DEBUG_SOURCE_THIRD_PARTY_KHR',0x8249)
GL_DEBUG_SOURCE_WINDOW_SYSTEM=_C('GL_DEBUG_SOURCE_WINDOW_SYSTEM',0x8247)
GL_DEBUG_SOURCE_WINDOW_SYSTEM_KHR=_C('GL_DEBUG_SOURCE_WINDOW_SYSTEM_KHR',0x8247)
GL_DEBUG_TYPE_DEPRECATED_BEHAVIOR=_C('GL_DEBUG_TYPE_DEPRECATED_BEHAVIOR',0x824D)
GL_DEBUG_TYPE_DEPRECATED_BEHAVIOR_KHR=_C('GL_DEBUG_TYPE_DEPRECATED_BEHAVIOR_KHR',0x824D)
GL_DEBUG_TYPE_ERROR=_C('GL_DEBUG_TYPE_ERROR',0x824C)
GL_DEBUG_TYPE_ERROR_KHR=_C('GL_DEBUG_TYPE_ERROR_KHR',0x824C)
GL_DEBUG_TYPE_MARKER=_C('GL_DEBUG_TYPE_MARKER',0x8268)
GL_DEBUG_TYPE_MARKER_KHR=_C('GL_DEBUG_TYPE_MARKER_KHR',0x8268)
GL_DEBUG_TYPE_OTHER=_C('GL_DEBUG_TYPE_OTHER',0x8251)
GL_DEBUG_TYPE_OTHER_KHR=_C('GL_DEBUG_TYPE_OTHER_KHR',0x8251)
GL_DEBUG_TYPE_PERFORMANCE=_C('GL_DEBUG_TYPE_PERFORMANCE',0x8250)
GL_DEBUG_TYPE_PERFORMANCE_KHR=_C('GL_DEBUG_TYPE_PERFORMANCE_KHR',0x8250)
GL_DEBUG_TYPE_POP_GROUP=_C('GL_DEBUG_TYPE_POP_GROUP',0x826A)
GL_DEBUG_TYPE_POP_GROUP_KHR=_C('GL_DEBUG_TYPE_POP_GROUP_KHR',0x826A)
GL_DEBUG_TYPE_PORTABILITY=_C('GL_DEBUG_TYPE_PORTABILITY',0x824F)
GL_DEBUG_TYPE_PORTABILITY_KHR=_C('GL_DEBUG_TYPE_PORTABILITY_KHR',0x824F)
GL_DEBUG_TYPE_PUSH_GROUP=_C('GL_DEBUG_TYPE_PUSH_GROUP',0x8269)
GL_DEBUG_TYPE_PUSH_GROUP_KHR=_C('GL_DEBUG_TYPE_PUSH_GROUP_KHR',0x8269)
GL_DEBUG_TYPE_UNDEFINED_BEHAVIOR=_C('GL_DEBUG_TYPE_UNDEFINED_BEHAVIOR',0x824E)
GL_DEBUG_TYPE_UNDEFINED_BEHAVIOR_KHR=_C('GL_DEBUG_TYPE_UNDEFINED_BEHAVIOR_KHR',0x824E)
GL_DISPLAY_LIST=_C('GL_DISPLAY_LIST',0x82E7)
GL_MAX_DEBUG_GROUP_STACK_DEPTH=_C('GL_MAX_DEBUG_GROUP_STACK_DEPTH',0x826C)
GL_MAX_DEBUG_GROUP_STACK_DEPTH_KHR=_C('GL_MAX_DEBUG_GROUP_STACK_DEPTH_KHR',0x826C)
GL_MAX_DEBUG_LOGGED_MESSAGES=_C('GL_MAX_DEBUG_LOGGED_MESSAGES',0x9144)
GL_MAX_DEBUG_LOGGED_MESSAGES_KHR=_C('GL_MAX_DEBUG_LOGGED_MESSAGES_KHR',0x9144)
GL_MAX_DEBUG_MESSAGE_LENGTH=_C('GL_MAX_DEBUG_MESSAGE_LENGTH',0x9143)
GL_MAX_DEBUG_MESSAGE_LENGTH_KHR=_C('GL_MAX_DEBUG_MESSAGE_LENGTH_KHR',0x9143)
GL_MAX_LABEL_LENGTH=_C('GL_MAX_LABEL_LENGTH',0x82E8)
GL_MAX_LABEL_LENGTH_KHR=_C('GL_MAX_LABEL_LENGTH_KHR',0x82E8)
GL_PROGRAM=_C('GL_PROGRAM',0x82E2)
GL_PROGRAM_KHR=_C('GL_PROGRAM_KHR',0x82E2)
GL_PROGRAM_PIPELINE=_C('GL_PROGRAM_PIPELINE',0x82E4)
GL_QUERY=_C('GL_QUERY',0x82E3)
GL_QUERY_KHR=_C('GL_QUERY_KHR',0x82E3)
GL_SAMPLER=_C('GL_SAMPLER',0x82E6)
GL_SAMPLER_KHR=_C('GL_SAMPLER_KHR',0x82E6)
GL_SHADER=_C('GL_SHADER',0x82E1)
GL_SHADER_KHR=_C('GL_SHADER_KHR',0x82E1)
GL_STACK_OVERFLOW=_C('GL_STACK_OVERFLOW',0x0503)
GL_STACK_OVERFLOW_KHR=_C('GL_STACK_OVERFLOW_KHR',0x0503)
GL_STACK_UNDERFLOW=_C('GL_STACK_UNDERFLOW',0x0504)
GL_STACK_UNDERFLOW_KHR=_C('GL_STACK_UNDERFLOW_KHR',0x0504)
GL_VERTEX_ARRAY=_C('GL_VERTEX_ARRAY',0x8074)
GL_VERTEX_ARRAY_KHR=_C('GL_VERTEX_ARRAY_KHR',0x8074)
@_f
@_p.types(None,_cs.GLDEBUGPROC,ctypes.c_void_p)
def glDebugMessageCallback(callback,userParam):pass
@_f
@_p.types(None,_cs.GLDEBUGPROCKHR,ctypes.c_void_p)
def glDebugMessageCallbackKHR(callback,userParam):pass
@_f
@_p.types(None,_cs.GLenum,_cs.GLenum,_cs.GLenum,_cs.GLsizei,arrays.GLuintArray,_cs.GLboolean)
def glDebugMessageControl(source,type,severity,count,ids,enabled):pass
@_f
@_p.types(None,_cs.GLenum,_cs.GLenum,_cs.GLenum,_cs.GLsizei,arrays.GLuintArray,_cs.GLboolean)
def glDebugMessageControlKHR(source,type,severity,count,ids,enabled):pass
@_f
@_p.types(None,_cs.GLenum,_cs.GLenum,_cs.GLuint,_cs.GLenum,_cs.GLsizei,arrays.GLcharArray)
def glDebugMessageInsert(source,type,id,severity,length,buf):pass
@_f
@_p.types(None,_cs.GLenum,_cs.GLenum,_cs.GLuint,_cs.GLenum,_cs.GLsizei,arrays.GLcharArray)
def glDebugMessageInsertKHR(source,type,id,severity,length,buf):pass
@_f
@_p.types(_cs.GLuint,_cs.GLuint,_cs.GLsizei,arrays.GLuintArray,arrays.GLuintArray,arrays.GLuintArray,arrays.GLuintArray,arrays.GLsizeiArray,arrays.GLcharArray)
def glGetDebugMessageLog(count,bufSize,sources,types,ids,severities,lengths,messageLog):pass
@_f
@_p.types(_cs.GLuint,_cs.GLuint,_cs.GLsizei,arrays.GLuintArray,arrays.GLuintArray,arrays.GLuintArray,arrays.GLuintArray,arrays.GLsizeiArray,arrays.GLcharArray)
def glGetDebugMessageLogKHR(count,bufSize,sources,types,ids,severities,lengths,messageLog):pass
@_f
@_p.types(None,_cs.GLenum,_cs.GLuint,_cs.GLsizei,arrays.GLsizeiArray,arrays.GLcharArray)
def glGetObjectLabel(identifier,name,bufSize,length,label):pass
@_f
@_p.types(None,_cs.GLenum,_cs.GLuint,_cs.GLsizei,arrays.GLsizeiArray,arrays.GLcharArray)
def glGetObjectLabelKHR(identifier,name,bufSize,length,label):pass
@_f
@_p.types(None,ctypes.c_void_p,_cs.GLsizei,arrays.GLsizeiArray,arrays.GLcharArray)
def glGetObjectPtrLabel(ptr,bufSize,length,label):pass
@_f
@_p.types(None,ctypes.c_void_p,_cs.GLsizei,arrays.GLsizeiArray,arrays.GLcharArray)
def glGetObjectPtrLabelKHR(ptr,bufSize,length,label):pass
@_f
@_p.types(None,_cs.GLenum,arrays.GLvoidpArray)
def glGetPointerv(pname,params):pass
@_f
@_p.types(None,_cs.GLenum,arrays.GLvoidpArray)
def glGetPointervKHR(pname,params):pass
@_f
@_p.types(None,_cs.GLenum,_cs.GLuint,_cs.GLsizei,arrays.GLcharArray)
def glObjectLabel(identifier,name,length,label):pass
@_f
@_p.types(None,_cs.GLenum,_cs.GLuint,_cs.GLsizei,arrays.GLcharArray)
def glObjectLabelKHR(identifier,name,length,label):pass
@_f
@_p.types(None,ctypes.c_void_p,_cs.GLsizei,arrays.GLcharArray)
def glObjectPtrLabel(ptr,length,label):pass
@_f
@_p.types(None,ctypes.c_void_p,_cs.GLsizei,arrays.GLcharArray)
def glObjectPtrLabelKHR(ptr,length,label):pass
@_f
@_p.types(None,)
def glPopDebugGroup():pass
@_f
@_p.types(None,)
def glPopDebugGroupKHR():pass
@_f
@_p.types(None,_cs.GLenum,_cs.GLuint,_cs.GLsizei,arrays.GLcharArray)
def glPushDebugGroup(source,id,length,message):pass
@_f
@_p.types(None,_cs.GLenum,_cs.GLuint,_cs.GLsizei,arrays.GLcharArray)
def glPushDebugGroupKHR(source,id,length,message):pass
