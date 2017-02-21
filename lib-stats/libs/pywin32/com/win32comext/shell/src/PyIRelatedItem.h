// This file declares the IRelatedItem Interface and Gateway for Python.
// Generated by makegw.py
// ---------------------------------------------------
//
// Interface Declaration

class PyIRelatedItem : public PyIUnknown
{
public:
	MAKE_PYCOM_CTOR(PyIRelatedItem);
	static IRelatedItem *GetI(PyObject *self);
	static PyComTypeObject type;

	// The Python methods
	static PyObject *GetItemIDList(PyObject *self, PyObject *args);
	static PyObject *GetItem(PyObject *self, PyObject *args);

protected:
	PyIRelatedItem(IUnknown *pdisp);
	~PyIRelatedItem();
};
// ---------------------------------------------------
//
// Gateway Declaration

class PyGRelatedItem : public PyGatewayBase, public IRelatedItem
{
protected:
	PyGRelatedItem(PyObject *instance) : PyGatewayBase(instance) { ; }
	PYGATEWAY_MAKE_SUPPORT2(PyGRelatedItem, IRelatedItem, IID_IRelatedItem, PyGatewayBase)



	// IRelatedItem
	STDMETHOD(GetItemIDList)(
		PIDLIST_ABSOLUTE * ppidl);

	STDMETHOD(GetItem)(
		IShellItem ** ppsi);

};
