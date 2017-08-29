import warnings
import threading 
import getpass
import re
import os

from robobrowser import RoboBrowser

warnings.filterwarnings('ignore', category=UserWarning, module='bs4')

def make_thread(task):
	def thread(*args, **kwargs):
		thread = threading.Thread(target=task, args=args, kwargs=kwargs)
		thread.start()
		return thread
	return thread
	
def login_msg():
	print('|       URI ONLINE JUDGE     |')
	print('|Login to download your codes|')			

def login_input():
	username = input('Username: ')
	password = getpass.getpass()
	return username, password
	
def login_urioj(username, password):
	url = 'https://www.urionlinejudge.com.br'
	browser = RoboBrowser()
	browser.open(url)
	form = browser.get_form(action='/judge/en/login')
	form['email'].value = username
	form['password'].value = password
	browser.submit_form(form)
	return browser

def is_logged(url):
	pattern = re.compile('https://www.urionlinejudge.com.br/judge/.+/login')
	return pattern.match(url) == None

def is_code_url(url):
	pattern = re.compile('/judge/pt/runs/code/.+')
	return pattern.match(url) != None

def find_all_code_href(browser):
	code_href = []
	for a in browser.find_all('a', href=True):
		if is_code_url(a['href']) and a.text == 'Accepted':
			code_href.append(a['href'])
	return code_href

def remove_extra_spaces(text):
    return re.sub(' +', ' ', text).strip()

def parse_code_info(browser):
	code_info = {}
	code_info['Codigo:'] = browser.find('pre').text
	meta_label = [remove_extra_spaces(info.text) for info in browser.find(id='information-code').find_all('dt')]
	meta_value = [remove_extra_spaces(info.text) for info in browser.find(id='information-code').find_all('dd')]
	for label, value in zip(meta_label, meta_value):
		if label == 'Problema:':
			problem_id, problem_name = value.split('-', 1)
			code_info['Id:'] = remove_extra_spaces(problem_id)
			code_info['Nome:'] = remove_extra_spaces(problem_name)
		else:
			code_info[label] = value
	return code_info

def get_file_ext(code_lan):
	if code_lan == 'C' or code_lan == 'C99':
		return '.c'
	elif code_lan == 'C#':
		return '.cs'
	elif code_lan == 'C++':
		return '.cpp'
	elif code_lan == 'Go':
		return '.go'
	elif code_lan == 'Java' or code_lan == 'Java 8':
		return '.java'
	elif code_lan == 'Python' or code_lan == 'Python 3':
		return '.py'
	elif code_lan == 'Ruby':
		return '.rb'
	elif code_lan == 'Scala':
		return '.scala'
	else:
		return '.idk'
	
def begin_comment(code_lan):
	if code_lan == 'Python':
		return '"""'
	elif code_lan == 'Python 3':
		return '"""'
	elif code_lan == 'Ruby':
		return '=begin'
	else:
		return '/*'
		
def end_comment(code_lan):
	if code_lan == 'Python':
		return '"""'
	elif code_lan == 'Python 3':
		return '"""'
	elif code_lan == 'Ruby':
		return '=end'
	else:
		return '*/'

def create_code_header(code_info):
	code_lan = code_info['Linguagem:']
	header = begin_comment(code_lan) + '\n'
	header += 'Nome:      ' + code_info['Nome:'] + '\n'
	header += 'ID:        ' + code_info['Id:'] + '\n'
	header += 'Resposta:  ' + code_info['Resposta:'] + '\n'
	header += 'Linguagem: ' + code_info['Linguagem:'] + '\n'
	header += 'Tempo:     ' + code_info['Tempo:'] + '\n'
	header += 'Tamanho:   ' + code_info['Tamanho:'] + '\n'
	header += 'Submissao: ' + code_info['Submissão:'] + '\n'
	header += end_comment(code_lan) + '\n'
	return header

def save_code(code_info, category, level):
	if not os.path.isdir('code'):
		os.mkdir('code')
	if not os.path.isdir('code/' + category):
		os.mkdir('code/' + category)
	if not os.path.isdir('code/' + category + '/' + level):
		os.mkdir('code/' + category + '/' + level)
	file_path = 'code/' + category + '/' + level + '/' + code_info['Id:'] + get_file_ext(code_info['Linguagem:'])
	if not os.path.exists(file_path):
		with open(file_path, 'a+') as code_file:
			code_file.write(create_code_header(code_info))
			code_file.write(code_info['Codigo:'])

def page_has_submisson(browser):
	return browser.find(id='error') == None

def find_category_and_level(browser):	
	level = browser.find('h3')['class'][-1]
	category = browser.find_all('a', class_='place-view ' + level)[-1].text
	return category, level

@make_thread
def save_page_code(problem_submission_url, username, password):
	browser = login_urioj(username, password)
	browser.open(problem_submission_url)
	code_href = find_all_code_href(browser)
	for href in code_href:
		print(href)
		browser.open('https://www.urionlinejudge.com.br' + href)
		code_info = parse_code_info(browser)
		browser.open('https://www.urionlinejudge.com.br/judge/pt/problems/view/' + code_info['Id:'])
		category, level = find_category_and_level(browser)
		save_code(code_info, category, level)

def main():
	login_msg()
	username, password = login_input()
	browser = login_urioj(username, password)
	if is_logged(browser.url):
		subm_url = 'https://www.urionlinejudge.com.br/judge/pt/runs?page='
		page_n = 1
		browser.open(subm_url + str(page_n))
		while page_has_submisson(browser):
			save_page_code(subm_url + str(page_n), username, password)
			page_n += 1
			browser.open(subm_url + str(page_n))
	else:
		print('Desculpe, usuario ou senha invalido.')
	
if __name__ == '__main__':
	main()
