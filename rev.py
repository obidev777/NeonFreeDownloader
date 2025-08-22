import socks
import socket
import uuid
import requests
from random import randint
from functools import partial
from bs4 import BeautifulSoup
import ProxyCloud as pc
from ProxyCloud import ProxyCloud
from requests_toolbelt import MultipartEncoder
from requests_toolbelt import MultipartEncoderMonitor
import requests_toolbelt as rt
import json
import time
import re
from requests.cookies import RequestsCookieJar

try:
    requests.packages.urllib3.disable_warnings()
except:pass

class CallingUpload:
    def __init__(self, func,filename,args):
        self.func = func
        self.args = args
        self.filename = filename
        self.time_start = time.time()
        self.time_total = 0
        self.speed = 0
        self.last_read_byte = 0
    def __call__(self,monitor):
        self.speed += monitor.bytes_read - self.last_read_byte
        self.last_read_byte = monitor.bytes_read
        tcurrent = time.time() - self.time_start
        self.time_total += tcurrent
        self.time_start = time.time()
        if self.time_total>=1:
            clock_time = (monitor.len - monitor.bytes_read) / (self.speed)
            if self.func:
                self.func(self.filename,monitor.bytes_read,monitor.len,self.speed,clock_time,self.args)
            self.time_total = 0
            self.speed = 0

class RevCli(object):
    def __init__(self,user='oby2001',passw='Obysoft2001@',proxy:ProxyCloud=None,
    host='https://rie.cujae.edu.cu/',type='RIE'):
        self.username = user
        self.password = passw
        self.host = host
        self.proxy = None
        if proxy:
            self.proxy = proxy.as_dict_proxy()
            print('Proxy: '+str(self.proxy))
        self.type=type
        self.session = requests.Session()
        self.headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.0'}
        self.serversid = 'http://pyobigram.file2link.ydns.eu:8900/get_sid'
        self.cookies = None

    def getsession(self):
        return self.session

    def login(self,rein=5):
        i = 0
        while i<rein:
            try:
                url = self.host + f'index.php/{self.type}/login'
                resp = self.session.get(url,proxies=self.proxy,headers=self.headers,verify=False)
                soup = BeautifulSoup(resp.text, "html.parser")

                csrfToken = soup.find('input',{'name':'csrfToken'})['value']

                payload = {}
                payload['csrfToken'] = csrfToken
                payload['source'] = ''
                payload['username'] = self.username
                payload['password'] = self.password
                payload['remember'] = '1'

                url += '/signIn'

                resp = self.session.post(url,data=payload,proxies=self.proxy,headers=self.headers,verify=False)

                if resp.url!=url:
                    #print('Login exito')
                    return True

                print('Login faild')
            except:pass
            i+=1
        return False

    def createID(self,count=8):
        from random import randrange
        map = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        id = ''
        i = 0
        while i<count:
            rnd = randrange(len(map))
            id+=map[rnd]
            i+=1
        return id

    def create_sid_apye(self):
        resp = self.session.get(f'{self.host}index.php/{self.type}/submission/wizard',proxies=self.proxy,headers=self.headers,verify=False)
        soup = BeautifulSoup(resp.text, "html.parser")
        inputs= soup.find_all('input')
        scripts = soup.find_all('script')

        csrfToken = ''
        for s in scripts:
                   js = s.next
                   lines = str(js).split(';')
                   if 'csrfToken' in js:
                           for lin in lines:
                               if 'csrfToken' in lin:
                                jsondata = '{' + str(lin).split('{',2)[1]
                                jsondata = json.loads(jsondata)
                                csrfToken = jsondata['csrfToken']
                                break

        pstr = '''csrfToken=c08c4ea0b72a398f9bd3e9da73ac91cf&submissionChecklist=1&locale=es_ES&sectionId=11&checklist-1=1&checklist-2=1&checklist-3=1&checklist-4=1&checklist-5=1&commentsToEditor=&userGroupId=116&copyrightNoticeAgree=1&privacyConsent=1&submitFormButton='''
        payload = {}
        tokens = pstr.split('&')
        for t in tokens:
            tt = t.split('=')
            key = ''
            value = ''
            if len(tt)>0:
                key = tt[0]
            if len(tt)>1:
                value = tt[1]
            if key:
                payload[key] = value

        payload['csrfToken'] = csrfToken

        resp = self.session.post(f'{self.host}index.php/{self.type}/submission/saveStep/1',proxies=self.proxy,headers=self.headers,verify=False)

        soup = BeautifulSoup(json.loads(resp.text)['content'], "html.parser")

        inputs = soup.find_all('input')

        csrfToken = soup.find('input',{'name':'csrfToken'})

        #print(inputs)
        for i in inputs:
            payload[i['name']] = i['value']


        self.session.post('https://rie.cujae.edu.cu/index.php/RIE/notification/fetchNotification',proxies=self.proxy,headers=self.headers,verify=False)

        payload['userGroupId'] = '14'
        payload['sectionId'] = '3'

        #print(payload)
        resp = self.session.post(f'{self.host}index.php/{self.type}/submission/saveStep/1',data=payload,proxies=self.proxy,headers=self.headers,verify=False)

        #print(resp.text)
        sidurl = json.loads(resp.text)['events'][0]['data']

        sid = sidurl.split('?')[1].split('#')[0].split('=')[1]
        #print(sid)
        return sid

    def create_sid_mendive_upr(self):
        resp = self.session.get(f'{self.host}index.php/{self.type}/submission/wizard',proxies=self.proxy,headers=self.headers,verify=False)
        soup = BeautifulSoup(resp.text, "html.parser")
        inputs= soup.find_all('input')
        scripts = soup.find_all('script')

        csrfToken = ''
        for s in scripts:
                   js = s.next
                   lines = str(js).split(';')
                   if 'csrfToken' in js:
                           for lin in lines:
                               if 'csrfToken' in lin:
                                jsondata = '{' + str(lin).split('{',2)[1]
                                jsondata = json.loads(jsondata)
                                csrfToken = jsondata['csrfToken']
                                break

        pstr = '''csrfToken=6f54c6d978191417c2b0a4850b4f28f9&submissionChecklist=1&locale=es_ES&sectionId=1&checklist-0=1&checklist-1=1&checklist-2=1&checklist-3=1&checklist-4=1&checklist-5=1&checklist-6=1&commentsToEditor=&userGroupId=14&copyrightNoticeAgree=1&privacyConsent=1&submitFormButton='''
        payload = {}
        tokens = pstr.split('&')
        for t in tokens:
            tt = t.split('=')
            key = ''
            value = ''
            if len(tt)>0:
                key = tt[0]
            if len(tt)>1:
                value = tt[1]
            if key:
                payload[key] = value

        payload['csrfToken'] = csrfToken

        resp = self.session.post(f'{self.host}index.php/{self.type}/submission/saveStep/1',data=payload,proxies=self.proxy,headers=self.headers,verify=False)

        #print(resp.text)
        sidurl = json.loads(resp.text)['events'][0]['data']

        sid = sidurl.split('?')[1].split('#')[0].split('=')[1]
        #print(sid)
        return sid

    def create_sid_opuntiabrava(self):
        resp = self.session.get(f'{self.host}index.php/{self.type}/submission/wizard',proxies=self.proxy,headers=self.headers,verify=False)
        soup = BeautifulSoup(resp.text, "html.parser")
        inputs= soup.find_all('input')
        scripts = soup.find_all('script')

        csrfToken = ''
        for s in scripts:
                   js = s.next
                   lines = str(js).split(';')
                   if 'csrfToken' in js:
                           for lin in lines:
                               if 'csrfToken' in lin:
                                jsondata = '{' + str(lin).split('{',2)[1]
                                jsondata = json.loads(jsondata)
                                csrfToken = jsondata['csrfToken']
                                break

        pstr = '''csrfToken=6f54c6d978191417c2b0a4850b4f28f9&submissionChecklist=1&locale=es_ES&sectionId=1&checklist-0=1&checklist-1=1&checklist-2=1&checklist-3=1&checklist-4=1&checklist-5=1&checklist-6=1&commentsToEditor=&userGroupId=14&copyrightNoticeAgree=1&privacyConsent=1&submitFormButton='''
        payload = {}
        tokens = pstr.split('&')
        for t in tokens:
            tt = t.split('=')
            key = ''
            value = ''
            if len(tt)>0:
                key = tt[0]
            if len(tt)>1:
                value = tt[1]
            if key:
                payload[key] = value

        payload['csrfToken'] = csrfToken

        resp = self.session.post(f'{self.host}index.php/{self.type}/submission/saveStep/1',data=payload,proxies=self.proxy,headers=self.headers,verify=False)

        #print(resp.text)
        sidurl = json.loads(resp.text)['events'][0]['data']

        sid = sidurl.split('?')[1].split('#')[0].split('=')[1]
        #print(sid)
        return sid

    def create_sid_stg(self):
        resp = self.session.get(f'{self.host}index.php/{self.type}/submission/wizard',proxies=self.proxy,headers=self.headers,verify=False)
        soup = BeautifulSoup(resp.text, "html.parser")
        inputs= soup.find_all('input')
        scripts = soup.find_all('script')

        csrfToken = ''
        for s in scripts:
                   js = s.next
                   lines = str(js).split(';')
                   if 'csrfToken' in js:
                           for lin in lines:
                               if 'csrfToken' in lin:
                                jsondata = '{' + str(lin).split('{',2)[1]
                                jsondata = json.loads(jsondata)
                                csrfToken = jsondata['csrfToken']
                                break

        pstr = '''csrfToken=c08c4ea0b72a398f9bd3e9da73ac91cf&submissionChecklist=1&locale=es_ES&sectionId=11&checklist-1=1&checklist-2=1&checklist-3=1&checklist-4=1&checklist-5=1&commentsToEditor=&userGroupId=116&copyrightNoticeAgree=1&privacyConsent=1&submitFormButton='''
        payload = {}
        tokens = pstr.split('&')
        for t in tokens:
            tt = t.split('=')
            key = ''
            value = ''
            if len(tt)>0:
                key = tt[0]
            if len(tt)>1:
                value = tt[1]
            if key:
                payload[key] = value

        payload['csrfToken'] = csrfToken

        resp = self.session.post(f'{self.host}index.php/{self.type}/submission/saveStep/1',proxies=self.proxy,headers=self.headers,verify=False)

        soup = BeautifulSoup(json.loads(resp.text)['content'], "html.parser")

        inputs = soup.find_all('input')

        csrfToken = soup.find('input',{'name':'csrfToken'})

        #print(inputs)
        for i in inputs:
            payload[i['name']] = i['value']


        self.session.post('https://rie.cujae.edu.cu/index.php/RIE/notification/fetchNotification',proxies=self.proxy,headers=self.headers,verify=False)

        payload['userGroupId'] = '116'
        payload['sectionId'] = '11'

        #print(payload)
        resp = self.session.post(f'{self.host}index.php/{self.type}/submission/saveStep/1',data=payload,proxies=self.proxy,headers=self.headers,verify=False)

        #print(resp.text)
        sidurl = json.loads(resp.text)['events'][0]['data']

        sid = sidurl.split('?')[1].split('#')[0].split('=')[1]
        #print(sid)
        return sid

    def create_sid_riecu(self):
        resp = self.session.get(f'{self.host}index.php/{self.type}/submission/wizard',proxies=self.proxy,headers=self.headers,verify=False)
        soup = BeautifulSoup(resp.text, "html.parser")
        inputs= soup.find_all('input')
        scripts = soup.find_all('script')

        csrfToken = ''
        for s in scripts:
                   js = s.next
                   lines = str(js).split(';')
                   if 'csrfToken' in js:
                           for lin in lines:
                               if 'csrfToken' in lin:
                                jsondata = '{' + str(lin).split('{',2)[1]
                                jsondata = json.loads(jsondata)
                                csrfToken = jsondata['csrfToken']
                                break

        pstr = '''csrfToken=c08c4ea0b72a398f9bd3e9da73ac91cf&submissionChecklist=1&locale=es_ES&sectionId=11&checklist-1=1&checklist-2=1&checklist-3=1&checklist-4=1&checklist-5=1&commentsToEditor=&userGroupId=116&copyrightNoticeAgree=1&privacyConsent=1&submitFormButton='''
        payload = {}
        tokens = pstr.split('&')
        for t in tokens:
            tt = t.split('=')
            key = ''
            value = ''
            if len(tt)>0:
                key = tt[0]
            if len(tt)>1:
                value = tt[1]
            if key:
                payload[key] = value

        payload['csrfToken'] = csrfToken

        resp = self.session.post(f'{self.host}index.php/{self.type}/submission/saveStep/1',proxies=self.proxy,headers=self.headers,verify=False)

        soup = BeautifulSoup(json.loads(resp.text)['content'], "html.parser")

        inputs = soup.find_all('input')

        csrfToken = soup.find('input',{'name':'csrfToken'})

        #print(inputs)
        for i in inputs:
            payload[i['name']] = i['value']


        self.session.post('https://rie.cujae.edu.cu/index.php/RIE/notification/fetchNotification',proxies=self.proxy,headers=self.headers,verify=False)

        payload['userGroupId'] = '14'
        payload['sectionId'] = '1'

        #print(payload)
        resp = self.session.post(f'{self.host}index.php/{self.type}/submission/saveStep/1',data=payload,proxies=self.proxy,headers=self.headers,verify=False)

        #print(resp.text)
        sidurl = json.loads(resp.text)['events'][0]['data']

        sid = sidurl.split('?')[1].split('#')[0].split('=')[1]
        #print(sid)
        return sid



    def get_sidinfo(self,last_iter=0):
        return json.loads(requests.get(self.serversid,json={'type':self.type,'iter':last_iter}).text)

    def test_sid(self,sid):
        tname = 'requirements.txt'
        upl = self.upload(tname,sid=sid)
        if upl:
            return True
        return False

    def upload(self,file,progressfunc=None,args=(),sid='735',rein=5):
        try:
            resp = self.session.get(self.host + f'index.php/{self.type}/submission/wizard/2?submissionId='+sid,proxies=self.proxy,headers=self.headers,verify=False)

            soup = BeautifulSoup(resp.text, "html.parser")

            scripts = soup.find_all('script')

            csrfToken = ''

            for s in scripts:
                js = s.next
                lines = str(js).split(';')
                if 'csrfToken' in js:
                    for lin in lines:
                        if 'csrfToken' in lin:
                            jsondata = '{' + str(lin).split('{',2)[1]
                            jsondata = json.loads(jsondata)
                            csrfToken = jsondata['csrfToken']
                    break
                pass

            of = open(file,'rb')
            b = uuid.uuid4().hex
            upload_data = {
                'fileStage':(None,'2'),
                'name[es_ES]':(None,file),
                }
            upload_file = {
                'file':(file,of,'application/octet-stream'),
                **upload_data
                }
            post_file_url = self.host + f'index.php/{self.type}/api/v1/submissions/{sid}/files'
            encoder = rt.MultipartEncoder(upload_file,boundary=b)
            progrescall = CallingUpload(progressfunc,file,args)
            callback = partial(progrescall)
            monitor = MultipartEncoderMonitor(encoder,callback)
            headers = {'X-Csrf-Token':csrfToken}
            resp = self.session.post(post_file_url, data=monitor,
                                     headers={**headers, "Content-Type": "multipart/form-data; boundary=" + b,
                                              **self.headers
                                              }, proxies=self.proxy, verify=False)
            jsondata = json.loads(resp.text)
            of.close()
            return jsondata['url']
        except Exception as ex:
            #print(str(ex))
            return None

    def create_sid(self):
        if 'uciencia' in self.host:
            return self.create_sid_uciencia()
        if 'aeco' in self.host:
            return self.create_sid_aeco()
        if 'apye' in self.host:
            return self.create_sid_apye()
        if 'e1' in self.host:
            return self.create_sid_e1()
        if 'mendive.upr' in self.host:
            return self.create_sid_mendive_upr()
        if 'regu' in self.host:
            return self.create_sid_regu()
        if 'riecu' in self.host:
            return self.create_sid_riecu()
        if 'serie' in self.host:
            return self.create_sid_serie()
        if 'stg' in self.host:
            return self.create_sid_stg()
        if 'tecedu' in self.host:
            return self.create_sid_tecedu()
        if 'opuntiabrava' in self.host:
            return self.create_sid_opuntiabrava()


    def create_sid_uciencia(self):
        resp = self.session.get(f'{self.host}index.php/{self.type}/submission/wizard', proxies=self.proxy,
                                headers=self.headers, verify=False)
        soup = BeautifulSoup(resp.text, "html.parser")
        inputs = soup.find_all('input')
        scripts = soup.find_all('script')
        csrfToken = ''
        for s in scripts:
            js = s.next
            lines = str(js).split(';')
            if 'csrfToken' in js:
                for lin in lines:
                    if 'csrfToken' in lin:
                        jsondata = '{' + str(lin).split('{', 2)[1]
                        jsondata = json.loads(jsondata)
                        csrfToken = jsondata['csrfToken']
                        break
        pstr = '''csrfToken=c08c4ea0b72a398f9bd3e9da73ac91cf&submissionChecklist=1&locale=es_ES&sectionId=11&checklist-1=1&checklist-2=1&checklist-3=1&checklist-4=1&checklist-5=1&commentsToEditor=&userGroupId=116&copyrightNoticeAgree=1&privacyConsent=1&submitFormButton='''
        payload = {}
        tokens = pstr.split('&')
        for t in tokens:
            tt = t.split('=')
            key = ''
            value = ''
            if len(tt) > 0:
                key = tt[0]
            if len(tt) > 1:
                value = tt[1]
            if key:
                payload[key] = value
        payload['csrfToken'] = csrfToken
        resp = self.session.post(f'{self.host}index.php/{self.type}/submission/saveStep/1', proxies=self.proxy,
                                 headers=self.headers, verify=False)
        soup = BeautifulSoup(json.loads(resp.text)['content'], "html.parser")
        inputs = soup.find_all('input')
        csrfToken = soup.find('input', {'name': 'csrfToken'})
        # print(inputs)
        for i in inputs:
            payload[i['name']] = i['value']
        self.session.post('https://rie.cujae.edu.cu/index.php/RIE/notification/fetchNotification',
                          proxies=self.proxy, headers=self.headers, verify=False)
        payload['userGroupId'] = '48'
        payload['sectionId'] = '1'
        # print(payload)
        resp = self.session.post(f'{self.host}index.php/{self.type}/submission/saveStep/1', data=payload,
                                 proxies=self.proxy, headers=self.headers, verify=False)
        # print(resp.text)
        sidurl = json.loads(resp.text)['events'][0]['data']
        sid = sidurl.split('?')[1].split('#')[0].split('=')[1]
        #print(sid)
        return sid

    def create_sid_regu(self):
        resp = self.session.get(f'{self.host}index.php/{self.type}/submission/wizard', proxies=self.proxy,
                                headers=self.headers, verify=False)
        soup = BeautifulSoup(resp.text, "html.parser")
        inputs = soup.find_all('input')
        scripts = soup.find_all('script')
        csrfToken = ''
        for s in scripts:
            js = s.next
            lines = str(js).split(';')
            if 'csrfToken' in js:
                for lin in lines:
                    if 'csrfToken' in lin:
                        jsondata = '{' + str(lin).split('{', 2)[1]
                        jsondata = json.loads(jsondata)
                        csrfToken = jsondata['csrfToken']
                        break
        pstr = '''csrfToken=c08c4ea0b72a398f9bd3e9da73ac91cf&submissionChecklist=1&locale=es_ES&sectionId=11&checklist-1=1&checklist-2=1&checklist-3=1&checklist-4=1&checklist-5=1&commentsToEditor=&userGroupId=116&copyrightNoticeAgree=1&privacyConsent=1&submitFormButton='''
        payload = {}
        tokens = pstr.split('&')
        for t in tokens:
            tt = t.split('=')
            key = ''
            value = ''
            if len(tt) > 0:
                key = tt[0]
            if len(tt) > 1:
                value = tt[1]
            if key:
                payload[key] = value
        payload['csrfToken'] = csrfToken
        resp = self.session.post(f'{self.host}index.php/{self.type}/submission/saveStep/1', proxies=self.proxy,
                                 headers=self.headers, verify=False)
        soup = BeautifulSoup(json.loads(resp.text)['content'], "html.parser")
        inputs = soup.find_all('input')
        csrfToken = soup.find('input', {'name': 'csrfToken'})
        # print(inputs)
        for i in inputs:
            payload[i['name']] = i['value']
        self.session.post('https://rie.cujae.edu.cu/index.php/RIE/notification/fetchNotification',
                          proxies=self.proxy, headers=self.headers, verify=False)
        payload['userGroupId'] = '31'
        payload['sectionId'] = '5'
        # print(payload)
        resp = self.session.post(f'{self.host}index.php/{self.type}/submission/saveStep/1', data=payload,
                                 proxies=self.proxy, headers=self.headers, verify=False)
        # print(resp.text)
        sidurl = json.loads(resp.text)['events'][0]['data']
        sid = sidurl.split('?')[1].split('#')[0].split('=')[1]
        #print(sid)
        return sid

    def create_sid_aeco(self):
        resp = self.session.get(f'{self.host}index.php/{self.type}/submission/wizard', proxies=self.proxy,
                                headers=self.headers, verify=False)
        soup = BeautifulSoup(resp.text, "html.parser")
        inputs = soup.find_all('input')
        scripts = soup.find_all('script')
        csrfToken = ''
        for s in scripts:
            js = s.next
            lines = str(js).split(';')
            if 'csrfToken' in js:
                for lin in lines:
                    if 'csrfToken' in lin:
                        jsondata = '{' + str(lin).split('{', 2)[1]
                        jsondata = json.loads(jsondata)
                        csrfToken = jsondata['csrfToken']
                        break
        pstr = '''csrfToken=c08c4ea0b72a398f9bd3e9da73ac91cf&submissionChecklist=1&locale=es_ES&sectionId=11&checklist-1=1&checklist-2=1&checklist-3=1&checklist-4=1&checklist-5=1&commentsToEditor=&userGroupId=116&copyrightNoticeAgree=1&privacyConsent=1&submitFormButton='''
        payload = {}
        tokens = pstr.split('&')
        for t in tokens:
            tt = t.split('=')
            key = ''
            value = ''
            if len(tt) > 0:
                key = tt[0]
            if len(tt) > 1:
                value = tt[1]
            if key:
                payload[key] = value
        payload['csrfToken'] = csrfToken
        resp = self.session.post(f'{self.host}index.php/{self.type}/submission/saveStep/1', proxies=self.proxy,
                                 headers=self.headers, verify=False)
        soup = BeautifulSoup(json.loads(resp.text)['content'], "html.parser")
        inputs = soup.find_all('input')
        csrfToken = soup.find('input', {'name': 'csrfToken'})
        # print(inputs)
        for i in inputs:
            payload[i['name']] = i['value']
        self.session.post('https://rie.cujae.edu.cu/index.php/RIE/notification/fetchNotification',
                          proxies=self.proxy, headers=self.headers, verify=False)
        payload['userGroupId'] = '31'
        payload['sectionId'] = '55'
        # print(payload)
        resp = self.session.post(f'{self.host}index.php/{self.type}/submission/saveStep/1', data=payload,
                                 proxies=self.proxy, headers=self.headers, verify=False)
        # print(resp.text)
        sidurl = json.loads(resp.text)['events'][0]['data']
        sid = sidurl.split('?')[1].split('#')[0].split('=')[1]
        #print(sid)
        return sid

    def create_sid_serie(self):
        resp = self.session.get(f'{self.host}index.php/{self.type}/submission/wizard', proxies=self.proxy,
                                headers=self.headers, verify=False)
        soup = BeautifulSoup(resp.text, "html.parser")
        inputs = soup.find_all('input')
        scripts = soup.find_all('script')
        csrfToken = ''
        for s in scripts:
            js = s.next
            lines = str(js).split(';')
            if 'csrfToken' in js:
                for lin in lines:
                    if 'csrfToken' in lin:
                        jsondata = '{' + str(lin).split('{', 2)[1]
                        jsondata = json.loads(jsondata)
                        csrfToken = jsondata['csrfToken']
                        break
        pstr = '''csrfToken=c08c4ea0b72a398f9bd3e9da73ac91cf&submissionChecklist=1&locale=es_ES&sectionId=11&checklist-1=1&checklist-2=1&checklist-3=1&checklist-4=1&checklist-5=1&commentsToEditor=&userGroupId=116&copyrightNoticeAgree=1&privacyConsent=1&submitFormButton='''
        payload = {}
        tokens = pstr.split('&')
        for t in tokens:
            tt = t.split('=')
            key = ''
            value = ''
            if len(tt) > 0:
                key = tt[0]
            if len(tt) > 1:
                value = tt[1]
            if key:
                payload[key] = value
        payload['csrfToken'] = csrfToken
        resp = self.session.post(f'{self.host}index.php/{self.type}/submission/saveStep/1', proxies=self.proxy,
                                 headers=self.headers, verify=False)
        soup = BeautifulSoup(json.loads(resp.text)['content'], "html.parser")
        inputs = soup.find_all('input')
        csrfToken = soup.find('input', {'name': 'csrfToken'})
        # print(inputs)
        for i in inputs:
            payload[i['name']] = i['value']

        payload['userGroupId'] = '13'
        #payload['sectionId'] = '55'
        payload['seriesid'] = '1'
        payload['categories[]'] = '1'
        payload['worktype'] = '2'
        # print(payload)
        resp = self.session.post(f'{self.host}index.php/{self.type}/submission/saveStep/1', data=payload,
                                 proxies=self.proxy, headers=self.headers, verify=False)
        # print(resp.text)
        sidurl = json.loads(resp.text)['events'][0]['data']
        sid = sidurl.split('?')[1].split('#')[0].split('=')[1]
        #print(sid)
        return sid

    def create_sid_e1(self):
        resp = self.session.get(f'{self.host}index.php/{self.type}/submission/wizard', proxies=self.proxy,
                                headers=self.headers, verify=False)
        soup = BeautifulSoup(resp.text, "html.parser")
        inputs = soup.find_all('input')
        scripts = soup.find_all('script')
        csrfToken = ''
        for s in scripts:
            js = s.next
            lines = str(js).split(';')
            if 'csrfToken' in js:
                for lin in lines:
                    if 'csrfToken' in lin:
                        jsondata = '{' + str(lin).split('{', 2)[1]
                        jsondata = json.loads(jsondata)
                        csrfToken = jsondata['csrfToken']
                        break
        pstr = '''csrfToken=c08c4ea0b72a398f9bd3e9da73ac91cf&submissionChecklist=1&locale=es_ES&sectionId=11&checklist-1=1&checklist-2=1&checklist-3=1&checklist-4=1&checklist-5=1&commentsToEditor=&userGroupId=116&copyrightNoticeAgree=1&privacyConsent=1&submitFormButton='''
        payload = {}
        tokens = pstr.split('&')
        for t in tokens:
            tt = t.split('=')
            key = ''
            value = ''
            if len(tt) > 0:
                key = tt[0]
            if len(tt) > 1:
                value = tt[1]
            if key:
                payload[key] = value
        payload['csrfToken'] = csrfToken
        resp = self.session.post(f'{self.host}index.php/{self.type}/submission/saveStep/1', proxies=self.proxy,
                                 headers=self.headers, verify=False)
        soup = BeautifulSoup(json.loads(resp.text)['content'], "html.parser")
        inputs = soup.find_all('input')
        csrfToken = soup.find('input', {'name': 'csrfToken'})
        # print(inputs)
        for i in inputs:
            payload[i['name']] = i['value']

        payload['userGroupId'] = '13'
        #payload['sectionId'] = '55'
        payload['seriesid'] = '1'
        payload['categories[]'] = '1'
        payload['worktype'] = '2'
        # print(payload)
        resp = self.session.post(f'{self.host}index.php/{self.type}/submission/saveStep/1', data=payload,
                                 proxies=self.proxy, headers=self.headers, verify=False)
        # print(resp.text)
        sidurl = json.loads(resp.text)['events'][0]['data']
        sid = sidurl.split('?')[1].split('#')[0].split('=')[1]
        #print(sid)
        return sid



    def create_sid_tecedu(self):
        resp = self.session.get(f'{self.host}index.php/{self.type}/submission/wizard', proxies=self.proxy,
                                headers=self.headers, verify=False)
        soup = BeautifulSoup(resp.text, "html.parser")
        inputs = soup.find_all('input')
        scripts = soup.find_all('script')
        csrfToken = ''
        for s in scripts:
            js = s.next
            lines = str(js).split(';')
            if 'csrfToken' in js:
                for lin in lines:
                    if 'csrfToken' in lin:
                        jsondata = '{' + str(lin).split('{', 2)[1]
                        jsondata = json.loads(jsondata)
                        csrfToken = jsondata['csrfToken']
                        break
        pstr = '''csrfToken=c08c4ea0b72a398f9bd3e9da73ac91cf&submissionChecklist=1&locale=es_ES&sectionId=11&checklist-1=1&checklist-2=1&checklist-3=1&checklist-4=1&checklist-5=1&commentsToEditor=&userGroupId=116&copyrightNoticeAgree=1&privacyConsent=1&submitFormButton='''
        payload = {}
        tokens = pstr.split('&')
        for t in tokens:
            tt = t.split('=')
            key = ''
            value = ''
            if len(tt) > 0:
                key = tt[0]
            if len(tt) > 1:
                value = tt[1]
            if key:
                payload[key] = value
        payload['csrfToken'] = csrfToken
        resp = self.session.post(f'{self.host}index.php/{self.type}/submission/saveStep/1', proxies=self.proxy,
                                 headers=self.headers, verify=False)
        soup = BeautifulSoup(json.loads(resp.text)['content'], "html.parser")
        inputs = soup.find_all('input')
        csrfToken = soup.find('input', {'name': 'csrfToken'})
        # print(inputs)
        for i in inputs:
            payload[i['name']] = i['value']
        self.session.post('https://rie.cujae.edu.cu/index.php/RIE/notification/fetchNotification',
                          proxies=self.proxy, headers=self.headers, verify=False)
        payload['userGroupId'] = '31'
        payload['sectionId'] = '2'
        # print(payload)
        resp = self.session.post(f'{self.host}index.php/{self.type}/submission/saveStep/1', data=payload,
                                 proxies=self.proxy, headers=self.headers, verify=False)
        # print(resp.text)
        sidurl = json.loads(resp.text)['events'][0]['data']
        sid = sidurl.split('?')[1].split('#')[0].split('=')[1]
        #print(sid)
        return sid

    def delete_sid(self,sid,csrfToken=''):
        if csrfToken == '':
            resp = self.session.get(f'{self.host}index.php/{self.type}/submission/wizard', proxies=self.proxy,
                                    headers=self.headers, verify=False)
            soup = BeautifulSoup(resp.text, "html.parser")
            inputs = soup.find_all('input')
            scripts = soup.find_all('script')
            
            for s in scripts:
                js = s.next
                lines = str(js).split(';')
                if 'csrfToken' in js:
                    for lin in lines:
                        if 'csrfToken' in lin:
                            jsondata = '{' + str(lin).split('{', 2)[1]
                            jsondata = json.loads(jsondata)
                            csrfToken = jsondata['csrfToken']
                            break
            pstr = '''csrfToken=c08c4ea0b72a398f9bd3e9da73ac91cf&submissionChecklist=1&locale=es_ES&sectionId=11&checklist-1=1&checklist-2=1&checklist-3=1&checklist-4=1&checklist-5=1&commentsToEditor=&userGroupId=116&copyrightNoticeAgree=1&privacyConsent=1&submitFormButton='''
            payload = {}
            tokens = pstr.split('&')
            for t in tokens:
                tt = t.split('=')
                key = ''
                value = ''
                if len(tt) > 0:
                    key = tt[0]
                if len(tt) > 1:
                    value = tt[1]
                if key:
                    payload[key] = value
            hdrs = {**self.headers,'X-Csrf-Token':csrfToken,'X-Http-Method-Override':'DELETE','X-Requested-With':'XMLHttpRequest'}
        resp = self.session.post(f'{self.host}index.php/{self.type}/api/v1/_submissions/{sid}', proxies=self.proxy,
                                headers=hdrs, verify=False)
        if resp.text == 'true':
            return True
        return False

    def delete_all_sid(self):
        try:
            resp = self.session.get(f'{self.host}index.php/{self.type}/submissions', proxies=self.proxy,
                                    headers=self.headers, verify=False)
            soup = BeautifulSoup(resp.text, "html.parser")
            submisions = json.loads(soup.find_all('script')[-2].text.split('"Page", ')[-1].replace(');\n\t',''))['components']['myQueue']['items']
            for subm in submisions:
                self.delete_sid(subm['id'])
            return True
        except:pass
        return False

    def get_sids(self):
        try:
            resp = self.session.get(f'{self.host}index.php/{self.type}/submissions', proxies=self.proxy,
                                    headers=self.headers, verify=False)
            soup = BeautifulSoup(resp.text, "html.parser")
            submisions = json.loads(soup.find_all('script')[-2].text.split('"Page", ')[-1].replace(');\n\t',''))['components']['myQueue']['items']
            sids = []
            for subm in submisions:
                sids.append(subm['id'])
            return sids
        except:pass
        return []

    def get_filesize_from_url(self,url):
        try:
            resp = self.session.get(url, proxies=self.proxy,
                                    headers=self.headers, verify=False,allow_redirects=True,stream=True)
            if 'Content-Length' in resp.headers:
                size = int(resp.headers['Content-Length'])
                return size
            else:
                return "File size not available in headers."
        except requests.RequestException as e:
            return f"An error occurred: {e}"

    def get_files_from_sid(self,submid,with_size=True,filter=None):
        try:
            resp = self.session.get(f'{self.host}index.php/{self.type}/submission/step/2?submissionId={submid}&sectionId=0', proxies=self.proxy,
                                    headers=self.headers, verify=False)
            data = json.loads(resp.json()['content'].split('\"items\":')[1].split(',\"options\":')[0])
            files = []
            for f in data:
                if filter:
                    if f['name'] != filter:continue
                host = self.host.replace('https://','').replace('/','')
                fileid = f['id']
                mkurl = f'https://{host}/index.php/{self.type}/$$$call$$$/api/file/file-api/download-file?submissionFileId={fileid}&submissionId={submid}&stageId=1'
                if with_size:
                    filesize = self.get_filesize_from_url(mkurl)
                else:
                    filesize = 0
                files.append({'name':f['name']['es_ES'],'url':mkurl,'filesize':filesize})
            return files
        except:pass
        return []

    def add_cookie_to_session(self,name: str,
        value: str,
        domain: str,
        path: str = "/",
        secure: bool = False,
        expires: int = None,
        http_only: bool = False
        ) -> None:
        if not isinstance(self.session.cookies, RequestsCookieJar):
            self.session.cookies = RequestsCookieJar()
        self.session.cookies.set(
            name=name,
            value=value,
            domain=domain,
            path=path,
            secure=secure,
            expires=expires,
        )
        #print(f"Cookie añadida: {name}={value} (Domain: {domain})")

#cli = RevCli('obysofttt','Obysoft2001@',host='https://opuntiabrava.ult.edu.cu/',type='opuntiabrava')
#loged = cli.login()
#if loged:
#    sids = cli.get_sids()
#    for sid in sids:
#        print(cli.get_files_from_sid(sid))
#    print('Finish')
#    print('loged')
#    sid = cli.create_sid_opuntiabrava()
#    print(sid)
#    url = cli.upload('requirements.txt',sid=sid)
#    print(url)
#print('finish')