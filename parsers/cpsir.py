# -*- coding: utf-8 -*-
import parser
import re, time
import requests
import logging

class CpsirParser(parser.SiteParser):
   name = "cps"

   def parse(self):
       self.encoding = 'UTF-8'
       self.viewState = ""


       # 1. Start session
       self.sess = requests.Session()
       self.sess.headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.112 Safari/537.36' }
       req = self.sess.get('https://dms.i-t-systems.ru/cpsir/patient/panel.xhtml')
       self.viewState = self.parse_viewState( req )

       items = []

       params = { "j_idt13": "j_idt13", "javax.faces.ViewState": self.viewState }
       # 2. Бюджет или платные
       if 'budget' in self.parser_params:
          params['j_idt13:j_idt16']=''
       else:
          params['j_idt13:j_idt19']=''

       req = self.sess.post( 'https://dms.i-t-systems.ru/cpsir/patient/panel.xhtml', data=params )
       self.viewState = self.parse_viewState(req)

       speciality = self.get_param('spec','')
       data = self.parse_specs( speciality, False )
       logging.debug( repr(data) )

       for spec in data:
           for doctor in spec['doctors']:
               for day in doctor['days']:
                   for slot in day['slots']:
                       items.append( "%s/%s/%s %s" % (spec['speciality'], doctor['name'], day['day'], slot['time'] ) )
       return items


   def parse_slots(self, day_id):
       items = []
       params = {
          'j_idt13': 'j_idt13',
          'j_idt13:j_idt17': '',
          'javax.faces.ViewState': self.viewState
       }
       params[day_id]=''
       req = self.sess.post( 'https://dms.i-t-systems.ru/cpsir/patient/selectDay.xhtml', data=params )

       filter_text = re.compile(u'<button id="(.*?)".*type="submit"><span class="ui-button-text">(.*?) время.*?<\/span>', re.I+re.M)
       for m in filter_text.finditer( req.text ):
           slot_id = m.group(1)
           slot_name = m.group(2)
           items.append(  {'time': slot_name, 'id': slot_id } )
       return items

   def parse_days(self, doctor_id):
       items = []
       # select doctor
       params = {
              "j_idt14": "j_idt14",
              "j_idt14": "appointmentDate_input:%s" % time.strftime('%d.%m.%y'),
              "j_idt14": "j_idt19_input:00:00",
              "j_idt14": "j_idt21_input:23:59" ,
              "j_idt14:j_idt28": "",
              "javax.faces.ViewState":       self.viewState
       }
       params[doctor_id] = ''
       
       # получаем список дат
       req=self.sess.post( 'https://dms.i-t-systems.ru/cpsir/patient/selectDoctor.xhtml', data=params )

       filter_text = re.compile(u'<button id="(.*?)".*?<span class="ui-button-text">(.*?) .*<\/span>', re.I+re.M )
       for m in filter_text.finditer( req.text ):
           day_id = m.group(1)
           day_name = m.group(2)
           slots = self.parse_slots(day_id)
           items.append(  {'day': day_name, 'id': day_id, 'slots': slots} )
       return items

   def parse_doctors(self, speciality, spec_id ):
       items = []

       # выбираем специальность
       params = {
          "javax.faces.partial.ajax": "true",
          "javax.faces.source": spec_id,
          "javax.faces.partial.execute": "@all",
          "speciality":"speciality",
          "options": 1,
          "last-name":                   speciality,
          "javax.faces.ViewState":       self.viewState
       }
       params[spec_id] = spec_id
       req = self.sess.post( 'https://dms.i-t-systems.ru/cpsir/patient/selectSpeciality.xhtml', data=params )
 
       # получаем список врачей
       req = self.sess.get( 'https://dms.i-t-systems.ru/cpsir/patient/selectDoctor.xhtml' )

       filter_text = re.compile(u'<button id="(.*?)".*?selector" type="submit"><span class="ui-button-text">(.*?) НОМЕР.*?<\/span', re.I+re.M)
       for m in filter_text.finditer(req.text):
           doctor_id = m.group(1)
           doctor = m.group(2)
           days = self.parse_days(doctor_id)
           items.append( {'id':doctor_id, 'name': doctor, 'days': days } )
       return items


   def parse_specs(self, speciality, viewAll=False):
       items = []

       # Получить список специальностей по названию
       params = {
           "javax.faces.partial.ajax": "true",
           "javax.faces.source": "last-name",
           "javax.faces.partial.execute": "last-name",
           "javax.faces.partial.render": "speciality_list",
           "javax.faces.behavior.event": "keyup",
           "javax.faces.partial.event": "keyup",
           "speciality":"speciality",
           "options": 1,
           "last-name":                   speciality,
           "javax.faces.ViewState":       self.viewState
       }
       req = self.sess.post( 'https://dms.i-t-systems.ru/cpsir/patient/selectSpeciality.xhtml', data=params )

       filter_text = re.compile(u'<button id="([^"]*)".*?<span class="ui-button-text">([^ ]+)[^<]*<\/span>', re.I+re.M )
       for m in filter_text.finditer( req.text ):
           id = m.group(1)
           text = m.group(2)

           doctors = self.parse_doctors(speciality, id)
           items.append(  {'speciality': text, 'id': id, 'doctors': doctors } )
       return items



   def parse_viewState(self,req):
       filter_text = re.compile(u'name="javax.faces.ViewState".*value="([^"]+)"', re.I+re.U+re.M )
       m = filter_text.search( req.text )
       if m:
          return m.group(1)
       return None
