// This file declares the IShellExtInit Interface and Gateway for Python.
// Generated by makegw.py
// ---------------------------------------------------
//
// Interface Declaration

class PyIShellExtInit : public PyIUnknown
{
public:
	MAKE_PYCOM_CTOR(PyIShellExtInit);
	static IShellExtInit *GetI(PyObject *self);
	static PyComTypeObject type;

	// The Python methods
	static PyObject *Initialize(PyObject *self, PyObject *args);

protected:
	PyIShellExtInit(IUnknown *pdisp);
	~PyIShellExtInit();
};
// ---------------------------------------------------
//
// Gateway Declaration

class PyGShellExtInit : public PyGatewayBase, public IShellExtInit
{
protected:
	PyGShellExtInit(PyObject *instance) : PyGatewayBase(instance) { ; }
	PYGATEWAY_MAKE_SUPPORT2(PyGShellExtInit, IShellExtInit, IID_IShellExtInit, PyGatewayBase)



	// IShellExtInit
	STDMETHOD(Initialize)(
		LPCITEMIDLIST pFolder,
		IDataObject * pDataObject,
		HKEY hkey);

};
