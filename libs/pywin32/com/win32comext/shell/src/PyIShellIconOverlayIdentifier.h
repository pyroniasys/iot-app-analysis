// This file declares the IShellIconOverlayIdentifier Interface and Gateway for Python.
// Generated by makegw.py
// ---------------------------------------------------
//
// Interface Declaration

class PyIShellIconOverlayIdentifier : public PyIUnknown
{
public:
	MAKE_PYCOM_CTOR(PyIShellIconOverlayIdentifier);
	static IShellIconOverlayIdentifier *GetI(PyObject *self);
	static PyComTypeObject type;

	// The Python methods
	static PyObject *IsMemberOf(PyObject *self, PyObject *args);
	static PyObject *GetOverlayInfo(PyObject *self, PyObject *args);
	static PyObject *GetPriority(PyObject *self, PyObject *args);

protected:
	PyIShellIconOverlayIdentifier(IUnknown *pdisp);
	~PyIShellIconOverlayIdentifier();
};
// ---------------------------------------------------
//
// Gateway Declaration

class PyGShellIconOverlayIdentifier : public PyGatewayBase, public IShellIconOverlayIdentifier
{
protected:
	PyGShellIconOverlayIdentifier(PyObject *instance) : PyGatewayBase(instance) { ; }
	PYGATEWAY_MAKE_SUPPORT2(PyGShellIconOverlayIdentifier, IShellIconOverlayIdentifier, IID_IShellIconOverlayIdentifier, PyGatewayBase)



	// IShellIconOverlayIdentifier
	STDMETHOD(IsMemberOf)(
		LPCWSTR path,
		DWORD attrib);

	STDMETHOD(GetOverlayInfo)(
		LPWSTR pwszIconFile, int cchMax, int * pIndex, DWORD * pdwFlags);

	STDMETHOD(GetPriority)(
		int __RPC_FAR * pri);

};
