// This file implements the IDebugExpressionContext Interface and Gateway for Python.
// Generated by makegw.py

#include "stdafx.h"
#include "PythonCOM.h"
#include "PythonCOMServer.h"
#include "PyIDebugExpressionContext.h"

// @doc - This file contains autoduck documentation
// ---------------------------------------------------
//
// Interface Implementation

PyIDebugExpressionContext::PyIDebugExpressionContext(IUnknown *pdisp):
	PyIUnknown(pdisp)
{
	ob_type = &type;
}

PyIDebugExpressionContext::~PyIDebugExpressionContext()
{
}

/* static */ IDebugExpressionContext *PyIDebugExpressionContext::GetI(PyObject *self)
{
	return (IDebugExpressionContext *)PyIUnknown::GetI(self);
}

// @pymethod |PyIDebugExpressionContext|ParseLanguageText|Description of ParseLanguageText.
PyObject *PyIDebugExpressionContext::ParseLanguageText(PyObject *self, PyObject *args)
{
	IDebugExpressionContext *pIDEC = GetI(self);
	if ( pIDEC == NULL )
		return NULL;
	// @pyparm <o unicode>|pstrCode||Description for pstrCode
	// @pyparm int|nRadix||Description for nRadix
	// @pyparm <o unicode>|pstrDelimiter||Description for pstrDelimiter
	// @pyparm int|dwFlags||Description for dwFlags
	PyObject *obpstrCode;
	PyObject *obpstrDelimiter;
	LPOLESTR pstrCode;
	UINT nRadix;
	LPOLESTR pstrDelimiter;
	DWORD dwFlags;
	IDebugExpression * ppe;
	if ( !PyArg_ParseTuple(args, "OiOi:ParseLanguageText", &obpstrCode, &nRadix, &obpstrDelimiter, &dwFlags) )
		return NULL;
	BOOL bPythonIsHappy = TRUE;
	if (!PyCom_BstrFromPyObject(obpstrCode, &pstrCode)) bPythonIsHappy = FALSE;
	if (!PyCom_BstrFromPyObject(obpstrDelimiter, &pstrDelimiter)) bPythonIsHappy = FALSE;
	if (!bPythonIsHappy) return NULL;
	HRESULT hr;
	PY_INTERFACE_PRECALL;
	hr = pIDEC->ParseLanguageText( pstrCode, nRadix, pstrDelimiter, dwFlags, &ppe );
	SysFreeString(pstrCode);
	SysFreeString(pstrDelimiter);
	PY_INTERFACE_POSTCALL;

	if ( FAILED(hr) )
		return OleSetOleError(hr);
	return PyCom_PyObjectFromIUnknown(ppe, IID_IDebugExpression, FALSE);
}

// @pymethod |PyIDebugExpressionContext|GetLanguageInfo|Description of GetLanguageInfo.
PyObject *PyIDebugExpressionContext::GetLanguageInfo(PyObject *self, PyObject *args)
{
	IDebugExpressionContext *pIDEC = GetI(self);
	if ( pIDEC == NULL )
		return NULL;
	BSTR pbstrLanguageName;
	IID pLanguageID;
	if ( !PyArg_ParseTuple(args, ":GetLanguageInfo") )
		return NULL;
	HRESULT hr;
	PY_INTERFACE_PRECALL;
	hr = pIDEC->GetLanguageInfo( &pbstrLanguageName, &pLanguageID );
	PY_INTERFACE_POSTCALL;

	if ( FAILED(hr) )
		return OleSetOleError(hr);
	PyObject *obpbstrLanguageName;
	PyObject *obpLanguageID;

	obpbstrLanguageName = MakeBstrToObj(pbstrLanguageName);
	obpLanguageID = PyWinObject_FromIID(pLanguageID);
	PyObject *pyretval = Py_BuildValue("OO", obpbstrLanguageName, obpLanguageID);
	SysFreeString(pbstrLanguageName);
	Py_XDECREF(obpbstrLanguageName);
	Py_XDECREF(obpLanguageID);
	return pyretval;
}

// @object PyIDebugExpressionContext|Description of the interface
static struct PyMethodDef PyIDebugExpressionContext_methods[] =
{
	{ "ParseLanguageText", PyIDebugExpressionContext::ParseLanguageText, 1 }, // @pymeth ParseLanguageText|Description of ParseLanguageText
	{ "GetLanguageInfo", PyIDebugExpressionContext::GetLanguageInfo, 1 }, // @pymeth GetLanguageInfo|Description of GetLanguageInfo
	{ NULL }
};

PyComTypeObject PyIDebugExpressionContext::type("PyIDebugExpressionContext",
		&PyIUnknown::type,
		sizeof(PyIDebugExpressionContext),
		PyIDebugExpressionContext_methods,
		GET_PYCOM_CTOR(PyIDebugExpressionContext));
// ---------------------------------------------------
//
// Gateway Implementation

STDMETHODIMP PyGDebugExpressionContext::ParseLanguageText(
		/* [in] */ LPCOLESTR pstrCode,
		/* [in] */ UINT nRadix,
		/* [in] */ LPCOLESTR pstrDelimiter,
		/* [in] */ DWORD dwFlags,
		/* [out] */ IDebugExpression __RPC_FAR *__RPC_FAR * ppe)
{
	PY_GATEWAY_METHOD;
	if (ppe==NULL) return E_POINTER;
	PyObject *obpstrCode;
	PyObject *obpstrDelimiter;
	obpstrCode = PyWinObject_FromOLECHAR(pstrCode);
	obpstrDelimiter = PyWinObject_FromOLECHAR(pstrDelimiter);
	PyObject *result;
	HRESULT hr=InvokeViaPolicy("ParseLanguageText", &result, "OiOi", obpstrCode, nRadix, obpstrDelimiter, dwFlags);
	Py_XDECREF(obpstrCode);
	Py_XDECREF(obpstrDelimiter);
	if (FAILED(hr)) return hr;
	// Process the Python results, and convert back to the real params
	PyObject *obppe;
	if (!PyArg_Parse(result, "O" , &obppe)) return PyCom_HandlePythonFailureToCOM(/*pexcepinfo*/);
	BOOL bPythonIsHappy = TRUE;
	if (!PyCom_InterfaceFromPyInstanceOrObject(obppe, IID_IDebugExpression, (void **)ppe, TRUE /* bNoneOK */))
		 bPythonIsHappy = FALSE;
	if (!bPythonIsHappy) hr = PyCom_HandlePythonFailureToCOM(/*pexcepinfo*/);
	Py_DECREF(result);
	return hr;
}

STDMETHODIMP PyGDebugExpressionContext::GetLanguageInfo(
		/* [out] */ BSTR __RPC_FAR * pbstrLanguageName,
		/* [out] */ GUID __RPC_FAR * pLanguageID)
{
	PY_GATEWAY_METHOD;
	PyObject *result;
	HRESULT hr=InvokeViaPolicy("GetLanguageInfo", &result);
	if (FAILED(hr)) return hr;
	// Process the Python results, and convert back to the real params
	PyObject *obpbstrLanguageName;
	PyObject *obpLanguageID;
	if (!PyArg_ParseTuple(result, "OO" , &obpbstrLanguageName, &obpLanguageID)) return PyCom_HandlePythonFailureToCOM(/*pexcepinfo*/);
	BOOL bPythonIsHappy = TRUE;
	if (!PyCom_BstrFromPyObject(obpbstrLanguageName, pbstrLanguageName)) bPythonIsHappy = FALSE;
	if (!PyWinObject_AsIID(obpLanguageID, pLanguageID)) bPythonIsHappy = FALSE;
	if (!bPythonIsHappy) hr = PyCom_HandlePythonFailureToCOM(/*pexcepinfo*/);
	Py_DECREF(result);
	return hr;
}
