// This file implements the IPersistStorage interface for Python.
// Generated by makegw.py
#include "stdafx.h"
#include "PythonCOM.h"
#include "PyIPersist.h"
#include "PyIPersistStorage.h"

// @doc - This file contains autoduck documentation

PyIPersistStorage::PyIPersistStorage(IUnknown *pdisp):
	PyIPersist(pdisp)
{
	ob_type = &type;
}

PyIPersistStorage::~PyIPersistStorage()
{
}

/* static */ IPersistStorage *PyIPersistStorage::GetI(PyObject *self)
{
	return (IPersistStorage *)PyIPersist::GetI(self);
}

// @pymethod int|PyIPersistStorage|IsDirty|Checks the object for changes since it was last saved.
PyObject *PyIPersistStorage::IsDirty(PyObject *self, PyObject *args)
{
	IPersistStorage *pIPS = GetI(self);
	if ( pIPS == NULL )
		return NULL;
	if ( !PyArg_ParseTuple(args, ":IsDirty") )
		return NULL;
	PY_INTERFACE_PRECALL;
	HRESULT hr = pIPS->IsDirty( );
	PY_INTERFACE_POSTCALL;
	if ( FAILED(hr) )
		return PyCom_BuildPyException(hr, pIPS, IID_IPersistStorage);
	return PyInt_FromLong(hr);
	// @rvalue S_OK (ie, 0)|The object has changed since it was last saved. 
	// @rvalue S_FALSE (ie, 1)|The object has not changed since the last save. 
}
// @pymethod |PyIPersistStorage|InitNew|Initializes a new object, providing a storage object to be used for the object.
PyObject *PyIPersistStorage::InitNew(PyObject *self, PyObject *args)
{
	IPersistStorage *pIPS = GetI(self);
	if ( pIPS == NULL )
		return NULL;
	// @pyparm <o PyIStorage>|PyIStorage||<o PyIStorage> for the new storage object to be initialized. The container creates a nested storage object in its storage object (see <om PyIStorage::CreateStorage>). Then, the container calls the <om PyIPersistStorage::WriteClassStg> function to initialize the new storage object with the object class identifier (CLSID).
	PyObject * obIStorage;
	if ( !PyArg_ParseTuple(args, "O:InitNew", &obIStorage) )
		return NULL;
	IStorage *pStg;
	if (!PyCom_InterfaceFromPyObject(obIStorage, IID_IStorage, (void **)&pStg, FALSE /* bNoneOK */))
		return NULL;

	PY_INTERFACE_PRECALL;
	HRESULT hr = pIPS->InitNew( pStg );
	pStg->Release();
	PY_INTERFACE_POSTCALL;
	if ( FAILED(hr) )
		return PyCom_BuildPyException(hr, pIPS, IID_IPersistStorage);
	Py_INCREF(Py_None);
	return Py_None;
}
// @pymethod |PyIPersistStorage|Load|Loads an object from its existing storage.
PyObject *PyIPersistStorage::Load(PyObject *self, PyObject *args)
{
	IPersistStorage *pIPS = GetI(self);
	if ( pIPS == NULL )
		return NULL;
	// @pyparm <o PyIStorage>|storage||Existing storage for the object.
	PyObject * obIStorage;
	if ( !PyArg_ParseTuple(args, "O:Load", &obIStorage) )
		return NULL;
	IStorage *pStg;
	if (!PyCom_InterfaceFromPyObject(obIStorage, IID_IStorage, (void **)&pStg, FALSE /* bNoneOK */))
		return NULL;

	PY_INTERFACE_PRECALL;
	HRESULT hr = pIPS->Load( pStg );
	pStg->Release();
	PY_INTERFACE_POSTCALL;
	if ( FAILED(hr) )
		return PyCom_BuildPyException(hr, pIPS, IID_IPersistStorage);
	Py_INCREF(Py_None);
	return Py_None;
}
// @pymethod |PyIPersistStorage|Save|Saves an object, and any nested objects that it contains, into the specified storage. The object is placed in NoScribble mode, and it must not write to the specified storage until it receives a call to its <om PyIPersistStorage::SaveCompleted> method.
PyObject *PyIPersistStorage::Save(PyObject *self, PyObject *args)
{
	IPersistStorage *pIPS = GetI(self);
	if ( pIPS == NULL )
		return NULL;
	// @pyparm <o PyIStorage>|PyIStorage||Storage for the object
	// @pyparm fSameAsLoad|int||Indicates whether the specified storage object is the current one.<nl>
	// This parameter is set to FALSE when performing a Save As or Save A Copy To operation or when performing a full save. In the latter case, this method saves to a temporary file, deletes the original file, and renames the temporary file.<nl>
	// This parameter is set to TRUE to perform a full save in a low-memory situation or to perform a fast incremental save in which only the dirty components are saved. 
	PyObject * obIStorage;
	BOOL fSameAsLoad;
	if ( !PyArg_ParseTuple(args, "Oi:Save", &obIStorage, &fSameAsLoad) )
		return NULL;
	IStorage *pStgSave;
	if (!PyCom_InterfaceFromPyObject(obIStorage, IID_IStorage, (void **)&pStgSave, FALSE /* bNoneOK */))
		return NULL;

	PY_INTERFACE_PRECALL;
	HRESULT hr = pIPS->Save( pStgSave, fSameAsLoad );
	pStgSave->Release();
	PY_INTERFACE_POSTCALL;
	if ( FAILED(hr) )
		return PyCom_BuildPyException(hr, pIPS, IID_IPersistStorage);
	Py_INCREF(Py_None);
	return Py_None;
}
// @pymethod |PyIPersistStorage|SaveCompleted|Notifies the object that it can revert from NoScribble or HandsOff mode, in which it must not write to its storage object, to Normal mode, in which it can. The object enters NoScribble mode when it receives an <om PyIPersistStorage::Save> call.
PyObject *PyIPersistStorage::SaveCompleted(PyObject *self, PyObject *args)
{
	IPersistStorage *pIPS = GetI(self);
	if ( pIPS == NULL )
		return NULL;
	// @pyparm <o PyIStorage>|PyIStorage||The current storage object
	PyObject * obIStorage;
	if ( !PyArg_ParseTuple(args, "O:SaveCompleted", &obIStorage) )
		return NULL;
	IStorage *pStgNew;
	if (!PyCom_InterfaceFromPyObject(obIStorage, IID_IStorage, (void **)&pStgNew, FALSE /* bNoneOK */))
		return NULL;

	PY_INTERFACE_PRECALL;
	HRESULT hr = pIPS->SaveCompleted( pStgNew );
	pStgNew->Release();
	PY_INTERFACE_POSTCALL;
	if ( FAILED(hr) )
		return PyCom_BuildPyException(hr, pIPS, IID_IPersistStorage);
	Py_INCREF(Py_None);
	return Py_None;
}
// @pymethod |PyIPersistStorage|HandsOffStorage|Instructs the object to release all storage objects that have been passed to it by its container and to enter HandsOff mode, in which the object cannot do anything and the only operation that works is a close operation.
PyObject *PyIPersistStorage::HandsOffStorage(PyObject *self, PyObject *args)
{
	IPersistStorage *pIPS = GetI(self);
	if ( pIPS == NULL )
		return NULL;
	if ( !PyArg_ParseTuple(args, ":HandsOffStorage") )
		return NULL;
	PY_INTERFACE_PRECALL;
	HRESULT hr = pIPS->HandsOffStorage( );
	PY_INTERFACE_POSTCALL;
	if ( FAILED(hr) )
		return PyCom_BuildPyException(hr, pIPS, IID_IPersistStorage);
	Py_INCREF(Py_None);
	return Py_None;
}
// @object PyIPersistStorage|A Python wrapper of a COM IPersistStorage interface.
// @comm The IPersistStorage interface defines methods that enable a container application to pass a storage object to one of its contained objects and to load and save the storage object. This interface supports the structured storage model, in which each contained object has its own storage that is nested within the container's storage.
static struct PyMethodDef PyIPersistStorage_methods[] =
{
	{ "IsDirty", PyIPersistStorage::IsDirty, 1 }, // @pymeth IsDirty|Checks the object for changes since it was last saved.
	{ "InitNew", PyIPersistStorage::InitNew, 1 }, // @pymeth InitNew|Initializes a new object, providing a storage object to be used for the object.
	{ "Load", PyIPersistStorage::Load, 1 }, // @pymeth Load|Loads an object from its existing storage.
	{ "Save", PyIPersistStorage::Save, 1 }, // @pymeth Save|Saves an object, and any nested objects that it contains, into the specified storage.
	{ "SaveCompleted", PyIPersistStorage::SaveCompleted, 1 }, // @pymeth SaveCompleted|Notifies the object that it can revert from NoScribble or HandsOff mode.
	{ "HandsOffStorage", PyIPersistStorage::HandsOffStorage, 1 }, // @pymeth HandsOffStorage|Instructs the object to release all storage objects that have been passed to it by its container and to enter HandsOff mode.
	{ NULL }
};

PyComTypeObject PyIPersistStorage::type("PyIPersistStorage",
		&PyIUnknown::type,// @base PyIPersistPropertyBag|PyIUnknown
		sizeof(PyIPersistStorage),
		PyIPersistStorage_methods,
		GET_PYCOM_CTOR(PyIPersistStorage));
