/* backup.c - the backup type
 *
 * Copyright (C) 2010-2015 Gerhard Häring <gh@ghaering.de>
 *
 * This file is part of pysqlite.
 *
 * This software is provided 'as-is', without any express or implied
 * warranty.  In no event will the authors be held liable for any damages
 * arising from the use of this software.
 *
 * Permission is granted to anyone to use this software for any purpose,
 * including commercial applications, and to alter it and redistribute it
 * freely, subject to the following restrictions:
 *
 * 1. The origin of this software must not be misrepresented; you must not
 *    claim that you wrote the original software. If you use this software
 *    in a product, an acknowledgment in the product documentation would be
 *    appreciated but is not required.
 * 2. Altered source versions must be plainly marked as such, and must not be
 *    misrepresented as being the original software.
 * 3. This notice may not be removed or altered from any source distribution.
 */

#include "module.h"
#include "backup.h"

void pysqlite_backup_dealloc(pysqlite_Backup* self)
{
    int rc;

    if (self->backup) {
        Py_BEGIN_ALLOW_THREADS
        rc = sqlite3_backup_finish(self->backup);
        Py_END_ALLOW_THREADS

        Py_DECREF(self->source_con);
        Py_DECREF(self->dest_con);

        self->backup = NULL;
    }

    Py_TYPE(self)->tp_free((PyObject*)self);
}

PyObject* pysqlite_backup_step(pysqlite_Backup* self, PyObject* args, PyObject* kwargs)
{
    int npages;

    if (!PyArg_ParseTuple(args, "i", &npages)) {
        return NULL;
    }

    int rc = sqlite3_backup_step(self->backup, npages);

    if (rc == SQLITE_DONE) {
        Py_RETURN_TRUE;
    } else if (rc == SQLITE_OK) {
        Py_RETURN_FALSE;
    } else {
        PyErr_SetString(pysqlite_OperationalError, sqlite3_errmsg(self->source_con->db));
        return NULL;
    }
}

static PyObject* pysqlite_backup_get_remaining(pysqlite_Backup* self, void* unused)
{
    return Py_BuildValue("i", sqlite3_backup_remaining(self->backup));
}

static PyObject* pysqlite_backup_get_pagecount(pysqlite_Backup* self, void* unused)
{
    return Py_BuildValue("i", sqlite3_backup_remaining(self->backup));
}

static PyGetSetDef pysqlite_backup_getset[] = {
    {"remaining",  (getter)pysqlite_backup_get_remaining, (setter)0},
    {"pagecount",  (getter)pysqlite_backup_get_pagecount, (setter)0},
    {NULL}
};

static PyMethodDef pysqlite_backup_methods[] = {
    {"step", (PyCFunction)pysqlite_backup_step, METH_VARARGS,
        PyDoc_STR("Copy pages to backup database.")},
    {NULL, NULL}
};

PyTypeObject pysqlite_BackupType = {
        PyVarObject_HEAD_INIT(NULL, 0)
        MODULE_NAME ".Backup",                          /* tp_name */
        sizeof(pysqlite_Backup),                        /* tp_basicsize */
        0,                                              /* tp_itemsize */
        (destructor)pysqlite_backup_dealloc,            /* tp_dealloc */
        0,                                              /* tp_print */
        0,                                              /* tp_getattr */
        0,                                              /* tp_setattr */
        0,                                              /* tp_compare */
        0,                                              /* tp_repr */
        0,                                              /* tp_as_number */
        0,                                              /* tp_as_sequence */
        0,                                              /* tp_as_mapping */
        0,                                              /* tp_hash */
        0,                                              /* tp_call */
        0,                                              /* tp_str */
        0,                                              /* tp_getattro */
        0,                                              /* tp_setattro */
        0,                                              /* tp_as_buffer */
        Py_TPFLAGS_DEFAULT,                             /* tp_flags */
        0,                                              /* tp_doc */
        0,                                              /* tp_traverse */
        0,                                              /* tp_clear */
        0,                                              /* tp_richcompare */
        0,                                              /* tp_weaklistoffset */
        0,                                              /* tp_iter */
        0,                                              /* tp_iternext */
        pysqlite_backup_methods,                        /* tp_methods */
        0,                                              /* tp_members */
        pysqlite_backup_getset,                         /* tp_getset */
        0,                                              /* tp_base */
        0,                                              /* tp_dict */
        0,                                              /* tp_descr_get */
        0,                                              /* tp_descr_set */
        0,                                              /* tp_dictoffset */
        (initproc)0,                                    /* tp_init */
        0,                                              /* tp_alloc */
        0,                                              /* tp_new */
        0                                               /* tp_free */
};

extern int pysqlite_backup_setup_types(void)
{
    pysqlite_BackupType.tp_new = PyType_GenericNew;
    return PyType_Ready(&pysqlite_BackupType);
}
