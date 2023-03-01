import urllib.request
import requests
import re
import argparse
from sys import stderr
import urllib3
urllib3.disable_warnings()


def banner():
    stderr.writelines("""
██╗   ██╗ █████╗       ██╗██████╗
██║   ██║██╔══██╗      ██║██╔══██╗
██║   ██║███████║█████╗██║██║  ██║
██║   ██║██╔══██║╚════╝██║██║  ██║
╚██████╔╝██║  ██║      ██║██████╔╝
 ╚═════╝ ╚═╝  ╚═╝      ╚═╝╚═════╝

██████╗  ██████╗ ███╗   ███╗ █████╗ ██╗███╗   ██╗███████╗
██╔══██╗██╔═══██╗████╗ ████║██╔══██╗██║████╗  ██║██╔════╝
██║  ██║██║   ██║██╔████╔██║███████║██║██╔██╗ ██║███████╗
██║  ██║██║   ██║██║╚██╔╝██║██╔══██║██║██║╚██╗██║╚════██║
██████╔╝╚██████╔╝██║ ╚═╝ ██║██║  ██║██║██║ ╚████║███████║
╚═════╝  ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝╚══════╝

> Get related domains / subdomains by looking at Google Analytics IDs
> Python version
> By @JosueEncinar

""")

def get_UA(gtm_tag):
    pattern = r"UA-\d+-\d+"
    try:
        u = urllib.request.urlopen(f"https://www.googletagmanager.com/gtm.js?id={gtm_tag}")
        data = u.read().decode(errors="ignore")
        match = set(re.findall(pattern, data))
        return list(match)
    except Exception as e:
        print(e)
        return None

def get_googletagmanager(url):
    gtm_pattern = r"GTM-[A-Z0-9]+"
    ua_pattern = r"UA-\d+-\d+"
    googletagmanager_pattern = r"googletagmanager\.com/ns\.html[^>]+></iframe>|<!-- (?:End )?Google Tag Manager -->|googletagmanager\.com/gtm\.js"

    try:
        text = requests.get(url,
                    headers={
                        'User-agent': 'Mozilla/5.0 (Linux; Android 10; SM-A205U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.86 Mobile Safari/537.36'
                        },
                    verify=False).text
    except Exception as e:
        print(e)

    if text:
        if re.findall(googletagmanager_pattern, text):
            gtms = set(re.findall(gtm_pattern, text))
            uas = set(re.findall(ua_pattern, text))
            return True, list(uas), list(gtms)

    return False, None, None

def clean_relationships(domains):
    all_domains = []
    for domain in domains:
        all_domains.append(domain.replace('/relationships/',''))
    return all_domains

def get_domains_from_builtwith(id):
    pattern = "/relationships/[a-z0-9\-\_\.]+\.[a-z]+"
    url = f"https://builtwith.com/relationships/tag/{id}"
    try:
        u = urllib.request.urlopen(url)
        data = u.read().decode(errors="ignore")
        return clean_relationships(re.findall(pattern, data))
    except:
        pass
    return []

def get_domains_from_hackertarget(id):
    url = f"https://api.hackertarget.com/analyticslookup/?q={id}"
    try:
        response = requests.get(url)
        if response.status_code == 200 and "API count exceeded" not in response.text:
            return response.text.split("\n")
    except:
        pass
    return []

def get_domains(id):
    all_domains = set()
    all_domains = all_domains.union(get_domains_from_builtwith(id))
    all_domains = all_domains.union(get_domains_from_hackertarget(id))
    return list(all_domains)

def show_data(tag, tag_type):
        print("")
        if tag_type == "ua":
            analytics_id = tag.split('-')
            analytics_id = "-".join(analytics_id[0:2])
            print(f">> {analytics_id}")
            domains = get_domains(analytics_id)
            if domains:
                for domain in domains:
                    print(f"|__ {domain}")
            else:
                print("|__ NOT FOUND")
            print("")
        elif tag_type == "gtm":
            print(f">> {tag}")
            domains = get_domains(tag)
            if domains:
                for domain in domains:
                    print(f"|__ {domain}")
            else:
                print("|__ NOT FOUND")
            print("")
if __name__ == "__main__":
    banner()
    parser = argparse.ArgumentParser()
    parser.add_argument('-u','--url', help="URL to extract Google Analytics ID",required=True)
    args = parser.parse_args()
    url = args.url
    if not args.url.startswith("http"):
        stderr.writelines("the URL has to have a schema (e.g http[s]://)")
    stderr.writelines(f"[+] Analyzing url: {args.url}\n")
    tagmanager, uas, gtms = get_googletagmanager(args.url)
    if tagmanager:
        if gtms:
            stderr.writelines(f"[+] Found GTM(s): {' '.join(str(i) for i in gtms)}\n")
            stderr.writelines("[+] Obtaining information from builtwith and hackertarget\n")
            for gtm in gtms:
                uas += get_UA(gtm)

                show_data(gtm, "gtm")
        if uas:
            stderr.writelines(f"[+] Found UA(s): {' '.join(str(i) for i in uas)}\n")
            stderr.writelines("[+] Obtaining information from builtwith and hackertarget\n")
            for ua in uas:
                show_data(ua, "ua")

        stderr.writelines("[+] Done! \n")
    else:
        stderr.writelines("[-] Google Tag Manager not detected\n")
