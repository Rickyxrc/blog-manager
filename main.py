import os, yaml, frontmatter, random, re, json
from colorama import Style, Fore, just_fix_windows_console
from urllib.parse import unquote, quote
import datetime
import argparse

just_fix_windows_console()

def to18(string):
    return f'{string:18}'

def rnd8():
    hexstr = '01234567890abcdef'
    res = []
    for _ in range(8):
        res.append(random.choice(hexstr))
    return ''.join(res)

def valid_hex8(hex_str):
    hexstr = '01234567890abcdef'
    if len(hex_str) != 8:
        return False
    for i in range(8):
        if not hex_str[i] in hex_str:
            return False
    return True

def to_valid_hex8(hex_str):
    if not valid_hex8():
        return rnd8()
    return hex_str

def create_dir_ifnot(path):
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))

def rename_ifnot(source, dest):
    create_dir_ifnot(dest)
    os.rename(source, dest)

config = yaml.safe_load(open('./_config.yaml', encoding='utf-8'))['blogmanager']

refactor = []

registered_refactor_method_print = {}

registered_refactor_method_print['dir.rename']              = lambda x : f"Rename dir {Fore.RED}\"{x['source']}\"{Style.RESET_ALL} to {Fore.GREEN}\"{x['dest']}\"{Style.RESET_ALL}"
registered_refactor_method_print['file.rename']             = lambda x : f"Rename file {Fore.RED}\"{x['source']}\"{Style.RESET_ALL} to {Fore.GREEN}\"{x['dest']}\"{Style.RESET_ALL}"
registered_refactor_method_print['post.frontmatter.change'] = lambda x : f"Change post {Fore.LIGHTBLACK_EX}\"{x['file']}\"{Style.RESET_ALL} frontmatter \"{x['key']}\" to {Fore.GREEN}\"{x['value']}\"{Style.RESET_ALL}"
registered_refactor_method_print['post.content.rename']     = lambda x : f"Rename {Fore.RED}\"{x['content']}\"{Style.RESET_ALL} in post {Fore.LIGHTBLACK_EX}\"{x['file']}\"{Style.RESET_ALL} to {Fore.GREEN}\"{x['value']}\"{Style.RESET_ALL}"
registered_refactor_method_print['dir.empty.del']           = lambda x : f"Delete empty dir {Fore.RED}\"{x['path']}\"{Style.RESET_ALL}"
registered_refactor_method_print['danger.exec']             = lambda x : (f"\"cd {x['path']} && {x['precommit']}\" exited with code ") + str(os.system(f'\"cd {x["path"]} && {x["precommit"]}\"')>>8)
registered_refactor_method_print['file.init']               = lambda x : f"Create {Fore.GREEN}{x['file']}{Style.RESET_ALL}"

def print_refactor_event(event_name:str, param:dict, preview:bool = True):
    if preview:
        print(f'{Fore.MAGENTA}{to18("Refactor Preview")}{Style.RESET_ALL}',end='')
    else:
        print(f'{Fore.MAGENTA}{to18("Refactor")}{Style.RESET_ALL}',end='')
    print(f'{registered_refactor_method_print.get(event_name, lambda x : f"Unknown event : {Fore.LIGHTBLACK_EX}{x}{Style.RESET_ALL}")(param)}',end='')
    print(f'{Style.RESET_ALL}')

def setv(obj, key, value):
    obj[key] = value
    return obj

def write_content(file, content):
    with open(file, 'w', encoding = 'utf-8') as write_stream:
        write_stream.write(content)

registered_refactor_method = {}
registered_refactor_method['post.frontmatter.change'] = lambda x : write_content(x['file'], frontmatter.dumps(setv(frontmatter.load(open(x['file'], encoding = 'utf-8')), x['key'], x['value'])))
registered_refactor_method['dir.rename']              = lambda x : rename_ifnot(x['source'], x['dest'])
registered_refactor_method['file.rename']             = lambda x : registered_refactor_method['dir.rename'](x)
registered_refactor_method['post.content.rename']     = lambda x : write_content(x['file'], frontmatter.dumps(frontmatter.load(open(x['file'], encoding = 'utf-8'))).replace(x['content'], x['value']))
registered_refactor_method['dir.empty.del']           = lambda x : os.rmdir(x['path'])
registered_refactor_method['danger.exec']             = lambda x : os.system(f"cd {x['path']} && {x['commit']}")
registered_refactor_method['file.init']               = lambda x : open(x['file'], 'w', encoding='utf-8').write(x['content'])

def do_refactor_event(event_name:str, param:dict):
    print_refactor_event(event_name, param, False)
    registered_refactor_method.get(event_name, lambda _: print(f"{Fore.YELLOW}No Refactor avaliable for event {event_name}{Style.RESET_ALL}"))(param)

def print_refactor():
    global refactor
    for name, param in refactor:
        print_refactor_event(name, param)

def do_refactor():
    global refactor
    for name, param in refactor:
        do_refactor_event(name, param)

def confirm_refactor():
    global refactor
    if refactor == []:
        return
    print_refactor()
    print(f'Confirm Refactor? [{Fore.RED}N{Style.RESET_ALL}/{Fore.GREEN}y{Style.RESET_ALL}]:', end='')
    res = input()
    if res.lower() == 'y' or res.lower() == 'yes':
        print(f'{Fore.GREEN}{to18("Confirmed Refactor")}{Style.RESET_ALL}')
        do_refactor()
    else:
        print(f'{Fore.RED}{to18("Cancelled Refactor")}{Style.RESET_ALL}')
    refactor = []

def add_event(event_name:str, param:dict):
    global refactor
    if not (event_name, param) in refactor:
        refactor.append((event_name, param))

def refactor_post_slug(filename, source, slug):
    print(f"{Fore.LIGHTBLACK_EX}{to18('Scanning')}{Style.RESET_ALL}", end='\r')
    add_event("post.frontmatter.change", {'file':filename, 'key':config['url_slug'], 'value':slug})
    add_event("post.content.rename", {'file':filename, 'content':source, 'value':slug})

def iterate_post():
    global config
    for file in os.listdir(config['blog_path']):
        filename = config['blog_path'] + file
        with open(filename, encoding = 'utf-8') as rf:
            image_ref = {}

            print(f"{Fore.LIGHTBLACK_EX}{to18('Scanning')}\"{filename}\"{Style.RESET_ALL}")
            rf_frontmatter = frontmatter.load(rf)
            sugg_slug = rf_frontmatter[config['url_slug']]
            if not valid_hex8(rf_frontmatter[config['url_slug']]):
                sugg_slug = rnd8()
                print(f"{Fore.BLUE}{to18('Incorrect SLUG')}{Style.RESET_ALL}{Fore.BLUE}\"{rf_frontmatter[config['url_slug']]:8}\"{Style.RESET_ALL}{Fore.LIGHTBLACK_EX} At {filename}{Style.RESET_ALL}")
                refactor_post_slug(filename, rf_frontmatter[config['url_slug']], sugg_slug)
            re_content = re.findall(rf'\({config["image_base_url"]}(\S+)/(\S+)\.(png|jpg|jpeg)', rf_frontmatter.content)
            for match in re_content:
                print(f"{Fore.LIGHTBLACK_EX}{to18('Referenced Image')}{Style.RESET_ALL} /{unquote(match[0])}/{unquote(match[1])}.{match[2]}")
                pathname = f"{unquote(match[0])}/{unquote(match[1])}.{match[2]}"

                if unquote(match[0]) != match[0] or unquote(match[1]) != match[1]:
                    print(f"{Fore.LIGHTBLACK_EX}{to18('Unquote URL')}{Style.RESET_ALL} /{match[0]}/{match[1]}.{match[2]}")
                    add_event("post.content.rename", {'file':filename, 'content':f"{match[0]}/{match[1]}.{match[2]}", 'value':pathname})

                if not valid_hex8(match[1]):
                    if image_ref.get(pathname, False):
                        print(f"{Fore.LIGHTBLACK_EX}{to18('Duplicated Refactor')}{Style.RESET_ALL}{Fore.BLUE}\"{rf_frontmatter[config['url_slug']]:8}\"{Style.RESET_ALL}{Fore.LIGHTBLACK_EX} At {filename}{Style.RESET_ALL}")
                        continue
                    image_ref[pathname] = True
                    print(f"{match[1]}")
                    sugg_name = f"{sugg_slug}/{rnd8()}.{match[2]}"
                    print(f"{Fore.BLUE}{to18('Incorrect Image ref')}{Style.RESET_ALL} {Fore.BLUE}/{pathname}{Style.RESET_ALL}")
                    add_event("file.rename", {'source': os.path.join(config['image_path'], pathname), 'dest':os.path.join(config['image_path'], sugg_name)})
                    add_event("post.content.rename", {'file':filename, 'content':pathname, 'value':sugg_name})
        confirm_refactor()

def clear_empty_dir():
    global arg
    for f in os.listdir(config['image_path']):
        if os.path.isdir(os.path.join(config['image_path'], f)) and os.listdir(os.path.join(config['image_path'], f)) == []:
            print(f"{Fore.BLUE}{to18('Empty dir')}{Style.RESET_ALL}{Fore.LIGHTBLACK_EX}\"{os.path.join(config['image_path'], f)}\"{Style.RESET_ALL}")
            add_event('dir.empty.del', {'path' : os.path.join(config['image_path'], f)})
    confirm_refactor()

def commit():
    global config, arg
    if type(config.get('commands', None)) == dict:
        for name in config['commands'].keys():
            obj = config['commands'][name]
            for req in ['commit', 'path']:
                if obj.get(req, None) == None:
                    print(f"{Fore.RED}{to18('Config Error')}Key \"{name}\" don\'t have prop \"{req}\"{Style.RESET_ALL}")
                    print(f"{Fore.RED}Aborted{Style.RESET_ALL}")
                    exit(3)
            add_event('danger.exec', {'path' : obj['path'] ,'precommit' : obj.get('precommit', ''), 'commit' : obj['commit']})
            confirm_refactor()

if __name__ == '__main__':
    global arg
    parser = argparse.ArgumentParser(description=f"blog-manager, A light tool to fix your blog image links", prog='main.py')
    operations = parser.add_mutually_exclusive_group(required=False)
    operations.add_argument('--no-confirm', action='store_true', help = "auto accept all changes (NOT safe)")
    operations.add_argument('--new-post', action='store_true', help = "create a new post")
    arg = parser.parse_args()

    if arg.new_post:
        name = input('post name:')
        front_matter = frontmatter.loads('')
        front_matter.metadata = {
            'title' : name,
            config['url_slug'] : rnd8(),
            'description' : input("description:"),
            'pubDatetime' : datetime.datetime.now() #.strftime("%Y-%m-%d %H:%M:%S")
        }
        add_event('file.init', {'file' : os.path.join(config['blog_path'], f'{name}.md'), 'content' : frontmatter.dumps(front_matter)})
        confirm_refactor()
        exit(0)
    else:
        iterate_post()
        do_refactor()
        clear_empty_dir()
        commit()
        exit(0)
