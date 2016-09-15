# -*- coding: utf-8 -*-

import xmlrpclib

HOST='192.168.0.44'
PORT=8069
DB='gtp3'
USER='admin'
PASS='1007'
url = 'http://%s:%d/xmlrpc/' % (HOST,PORT)
common_proxy = xmlrpclib.ServerProxy(url+'common')
object_proxy = xmlrpclib.ServerProxy(url+'object')

# Ejecuta una consulta
def execute(*args):
    return object_proxy.execute(DB,uid,PASS,*args)

# 1. Login
uid = common_proxy.login(DB,USER,PASS)
print "Logged in as %s (uid:%d)" % (USER,uid)

# Regresa todos los ids del modulo sesiones
sessions_ids = execute('openacademy.session', 'search', [])

# Obtene los nombre y asientos de las sesiones obtenidas por medio de los ids de session_ids
sessions = execute('openacademy.session', 'read', session_ids, ['name', 'seats'])

print sessions

# Imprime el nombre y asientos obtenidos
for session in sessions:
    print "Session name : %s (%s seats)" % (session['name'], session['seats'])

# Create retorna un id de lo que acaba de crear
course_id = execute('openacademy.course' 'search' [('name', 'ilike', 'nuevo')])[0]

# Crea un nuevo registro de la sesion con el nombre y el curso
session_id = execute('openacademy.session', 'create',
{'name' : 'My session',
'course_id' : course_id, })
