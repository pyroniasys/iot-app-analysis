// This file declares the IPersistFolder Interface and Gateway for Python.
// Generated by makegw.py
// ---------------------------------------------------
//
// Interface Declaration

class PyIPersistFolder : public PyIPersist
{
public:
	MAKE_PYCOM_CTOR(PyIPersistFolder);
	static IPersistFolder *GetI(PyObject *self);
	static PyComTypeObject type;

	// The Python methods
	static PyObject *Initialize(PyObject *self, PyObject *args);

protected:
	PyIPersistFolder(IUnknown *pdisp);
	~PyIPersistFolder();
};
// ---------------------------------------------------
//
// Gateway Declaration

class PyGPersistFolder : public PyGPersist, public IPersistFolder
{
protected:
	PyGPersistFolder(PyObject *instance) : PyGPersist(instance) { ; }
	PYGATEWAY_MAKE_SUPPORT2(PyGPersistFolder, IPersistFolder, IID_IPersistFolder, PyGPersist)

	// IPersist
	STDMETHOD(GetClassID)(
            /* [out] */ CLSID __RPC_FAR *pClassID);

	// IPersistFolder
	STDMETHOD(Initialize)(
		LPCITEMIDLIST pidl);

};

// IPersistFolder2
//
// Interface Declaration

class PyIPersistFolder2 : public PyIPersistFolder
{
public:
	MAKE_PYCOM_CTOR(PyIPersistFolder2);
	static IPersistFolder2 *GetI(PyObject *self);
	static PyComTypeObject type;

	// The Python methods
	static PyObject *GetCurFolder(PyObject *self, PyObject *args);

protected:
	PyIPersistFolder2(IUnknown *pdisp);
	~PyIPersistFolder2();
};
// ---------------------------------------------------
//
// Gateway Declaration

class PyGPersistFolder2 : public PyGPersistFolder, public IPersistFolder2
{
protected:
	PyGPersistFolder2(PyObject *instance) : PyGPersistFolder(instance) { ; }
	PYGATEWAY_MAKE_SUPPORT2(PyGPersistFolder2, IPersistFolder2, IID_IPersistFolder2, PyGPersistFolder)

	// IPersist
	STDMETHOD(GetClassID)(
            /* [out] */ CLSID __RPC_FAR *pClassID);

	// IPersistFolder
	STDMETHOD(Initialize)(
		LPCITEMIDLIST pidl);

	// IPersistFolder2
	STDMETHOD(GetCurFolder)(
		PIDLIST_ABSOLUTE * ppidl);

};