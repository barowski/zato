# -*- coding: utf-8 -*-

"""
Copyright (C) 2011 Dariusz Suchojad <dsuch at gefira.pl>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# stdlib
from traceback import format_exc
from uuid import uuid4

# lxml
from lxml import etree
from lxml.objectify import Element

# validate
from validate import is_boolean

# Zato
from zato.common import ZatoException, ZATO_OK
from zato.common.odb.model import Cluster, TechnicalAccount
from zato.common.util import TRACE1, tech_account_password
from zato.server.service.internal import _get_params, AdminService

class GetDefinitionList(AdminService):
    """ Returns a list of technical accounts defined in the ODB. The items are
    sorted by the 'name' attribute.
    """
    def handle(self, *args, **kwargs):
        
        definition_list = Element('definition_list')
        
        payload = kwargs.get('payload')
        request_params = ['id']
        params = _get_params(payload, request_params, 'cluster.')
        
        q = self.server.odb.query(TechnicalAccount).\
                    order_by(TechnicalAccount.name).\
                    filter(Cluster.id==params['id'])

        for definition in q.all():

            definition_elem = Element('definition')
            
            definition_elem.id = definition.id
            definition_elem.name = definition.name
            definition_elem.is_active = definition.is_active

            definition_list.append(definition_elem)

        return ZATO_OK, etree.tostring(definition_list)
    
class GetByID(AdminService):
    """ Returns a technical account of a given ID.
    """
    def handle(self, *args, **kwargs):
        
        payload = kwargs.get('payload')
        request_params = ['tech_account_id']
        params = _get_params(payload, request_params, 'data.')
        
        tech_account = self.server.odb.query(TechnicalAccount.id, 
                                             TechnicalAccount.name, 
                                             TechnicalAccount.is_active).\
            filter(TechnicalAccount.id==params['tech_account_id']).one()
        
        tech_account_elem = Element('tech_account')
        tech_account_elem.id = tech_account.id;
        tech_account_elem.name = tech_account.name;
        tech_account_elem.is_active = tech_account.is_active;
        
        return ZATO_OK, etree.tostring(tech_account_elem)
    
class Create(AdminService):
    """ Creates a new technical account.
    """
    def handle(self, *args, **kwargs):
        
        payload = kwargs.get('payload')
        request_params = ['cluster_id', 'name', 'is_active']
        params = _get_params(payload, request_params, 'data.')
        
        cluster_id = params['cluster_id']
        name = params['name']
        
        cluster = self.server.odb.query(Cluster).filter_by(id=cluster_id).first()
        
        salt = uuid4().hex
        password = tech_account_password(uuid4().hex, salt)
        
        # Let's see if we already have an account of that name before committing
        # any stuff into the database.
        existing_one = self.server.odb.query(TechnicalAccount).\
            filter(Cluster.id==cluster_id).\
            filter(TechnicalAccount.name==name).first()
        
        if existing_one:
            raise Exception('Technical account [{0}] already exists on this cluster'.format(name))
        
        tech_account_elem = Element('tech_account')
        
        try:
            tech_account = TechnicalAccount(None, name, password, salt, params['is_active'], cluster=cluster)
            self.server.odb.add(tech_account)
            self.server.odb.commit()
            
            tech_account_elem.id = tech_account.id
            
        except Exception, e:
            msg = "Could not create a technical account, e=[{e}]".format(e=format_exc(e))
            self.logger.error(msg)
            self.server.odb.rollback()
            
            raise 
        
        return ZATO_OK, etree.tostring(tech_account_elem)
    

class Edit(AdminService):
    """ Updates an existing technical account.
    """
    def handle(self, *args, **kwargs):
        
        payload = kwargs.get('payload')
        request_params = ['cluster_id', 'tech_account_id', 'name', 'is_active']
        params = _get_params(payload, request_params, 'data.')
        
        cluster_id = params['cluster_id']
        tech_account_id = params['tech_account_id']
        name = params['name']
        
        existing_one = self.server.odb.query(TechnicalAccount).\
            filter(Cluster.id==cluster_id).\
            filter(TechnicalAccount.name==name).\
            filter(TechnicalAccount.id != tech_account_id).\
            first()
        
        if existing_one:
            raise Exception('Technical account [{0}] already exists on this cluster'.format(name))
        
        tech_account = self.server.odb.query(TechnicalAccount).\
            filter(TechnicalAccount.id==tech_account_id).one()
        
        tech_account.name = name
        tech_account.is_active = is_boolean(params['is_active'])
        
        try:
            self.server.odb.add(tech_account)
            self.server.odb.commit()
        except Exception, e:
            msg = "Could not update the technical account, e=[{e}]".format(e=format_exc(e))
            self.logger.error(msg)
            self.server.odb.rollback()
            
            raise 
        
        return ZATO_OK, ''