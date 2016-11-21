import urllib2, urllib, socket, json, cookielib, os, string
from cStringIO import StringIO
import codecs
from optparse import OptionParser
from BeautifulSoup import BeautifulSoup


def readJsonObjFromFile(file_name, path):
    f = open(file_name, "r")
    s = f.read()
    obj = json.loads(s)
    
    if path is None:
        return obj
    else:
        return getElementFromJson(obj, path)

    
def getElementFromJson(json_obj, path):
    current_obj = json_obj
    result = None
    tmps = path.split('->')
    num = len(tmps)
    
    sec_point = 0
    while sec_point < num:
        section = tmps[sec_point]
        if current_obj.get(section):
            if sec_point == (num -1):
                result = current_obj[section]
            else:
                current_obj = current_obj[section]
            sec_point += 1
        else:
            #print "no content in this section: ", section
            break
    
    return result



def sendRequest(opener, url, param, header, outputfile):
    #Encode the parameter
    #data_encoded = urllib.urlencode(param)
    if param is not None:
        #data_encoded = urllib.quote_plus(param)
        data_encoded = urllib.urlencode(param)
  
    if header is None:
        if param is None:
            req = urllib2.Request(url)
        else:
            req = urllib2.Request(url, data_encoded)
    else:
        req = urllib2.Request(url, data_encoded, header) 

    response = opener.open(req)
    the_page = response.read()
    if outputfile is not None:
        open(outputfile, "w").write(the_page)
        
    return the_page

#loadPage(opener, login_url, login_data, header)
def loadPage(opener, url, data, header):
        
        data_encoded = urllib.urlencode(data)
        print 'Data Encoded : ', data_encoded
        try:
#            if header is None:
#                if data is None:
#                    req = urllib2.Request(url)
#                else:
#                    req = urllib2.Request(url, data)
#            else:
#                req = urllib2.Request(url, data, header)
        
            if data is not None:
                response = opener.open(url, data)
            else:
                response = opener.open(url)
                
            response = opener.open(req)   
            return ''.join(response.readlines())
        except Exception as e:
            print 'Exception loadPage ', e



def login(opener, config_file, output_file):
    
    header = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip,deflate,sdch",
        "Accept-Language": "en-US,en;q=0.8",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded",
        "Host": "www.linkedin.com",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.65 Safari/537.36",
        "X-IsAJAXForm": "1",
        "X-Requested-With": "XMLHttpRequest"
    }
    
    username = readJsonObjFromFile(config_file, "login->username")
    password = readJsonObjFromFile(config_file, "login->password")
    
    login_url = "https://www.linkedin.com/uas/login-submit"
    
#    login_param = {    'session_key': username,    'session_password': password    }
#    
#    #                        (opener, url, param, header, outputfile)
#    res_content = sendRequest(opener, login_url, login_param, header)
#    #print res_content
#    soup = BeautifulSoup(res_content)
#    print soup.find("title")
#    return

    """
      Handle login. This should populate our cookie jar.
    """
    #html = loadPage(opener, "https://www.linkedin.com/", None, None)
    html = sendRequest(opener, "https://www.linkedin.com/", None, None, None)
    soup = BeautifulSoup(html)
    print 'Login Page : ',soup.find("title")
    csrf = soup.find(id="loginCsrfParam-login")['value']

    login_param = {    'session_key': username, 'session_password': password, 'loginCsrfParam': csrf,   }

    #print 'Login Params : ', login_param
    
    html = loadPage(opener, login_url, login_param, header)
    #html = sendRequest(opener, login_url, login_param, header, None)
    output = open(output_file, "ab")
    output.write(html)
    output.close()
    soup = BeautifulSoup(html)
    print soup.find("title")
    return



                  #  (opener, config_file, output_file)
def search_linkedin(opener, config_file, output_file):
    page_num = 1
    result_count = 1
    person_info = []
    output = open(output_file, "ab")
    
    #output.write("@RELATION PERSON\n")
    #output.write("@DATA\n")
    
    #result_count = searchPage(opener, config_file, page_num, person_info, temp_dir, output)
    
    search_url = "http://www.linkedin.com/vsearch/pj"
    
    search_array = readJsonObjFromFile(config_file, "searchRules")
    search_param = {}
    if search_array is not None:
        num = len(search_array)
        
        if num > 0:
            for item in search_array:
                search_param[getElementFromJson(item, "fieldName")] = getElementFromJson(item, "fieldValue")
            search_param['page_num'] = page_num

        else:
            print "search rules cannot be empty"
            #Exception to be Raised
            return 0
    else:
        print "search rules cannot be None"
        #Exception to be Raised
        return 0
    
    ###Request to Search
    res_content = sendRequest(opener, search_url, search_param, None, None)
    output.write(res_content)
    output.close()
    json_obj = json.loads(res_content)
    
    resultCount = getElementFromJson(json_obj, 'content->page->voltron_unified_search_json->search->baseData->resultCount')
    print "result count is: " , resultCount
    
    return 
    '''
    if resultCount > 0:

        results = getElementFromJson(json_obj, 'content->page->voltron_unified_search_json->search->results') 
        if results is not None:
            num = len(results)
            if num > 0:
                for item in results:
                    person = getElementFromJson(item, 'person')
                    processPerson(opener, person, person_info, temp_dir, output_file)
            else:
                resultCount = 0
        else:
            resultCount = 0

    return resultCount
    '''
    


if __name__ == '__main__' :
    #Default Options
    config_file = "config/config.json"
    cookie_file = "cookie/cookies.txt"
    output_file = "op/op.json" 
    #Parser Config for Command Line
    parser = OptionParser()
    parser.add_option( '--config-file', dest = 'config_file', help = 'configuration file in json Format')
    parser.add_option('--cookie-file', dest = 'cookie_file', help = 'Cookie File In Mozilla Cookie Format')
    parser.add_option('--output-file', dest = 'output_file', help = 'Output Directory for Storing Search Data')
    (options, args) = parser.parse_args()
    
    if options.config_file is not None:
        config_file = str(options.config_file)
    if options.cookie_file is not None:
        cookie_file = str(options.cookie_file)
    if options.output_file is not None:
        output_file = str(options.output_file)
    #return config_file, output_file, temp_dir
    
    #Configure connection
    timeout = 30
    socket.setdefaulttimeout(timeout)
    #cookie_jar = cookielib.LWPCookieJar()
    cookie_jar = cookielib.MozillaCookieJar()
    
    if os.path.isfile(cookie_file):
        cookie_jar.load(cookie_file)
    else:
        #Raise Error and Log
        print 'Cannot Find : %s ',cookie_file
    
    cookie = urllib2.HTTPCookieProcessor(cookie_jar)
    #Connection Object
    opener = urllib2.build_opener(cookie)
    urllib2.install_opener(opener)
    
    #Login with Credentials
    login(opener, config_file, output_file)
    
    #Search the LinkedIn People Search
    #search_linkedin(opener, config_file, output_file)
    