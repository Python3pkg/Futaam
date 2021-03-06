#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
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
import os
import sys
import locale
import urllib.request, urllib.error, urllib.parse
import threading
import getpass
from time import sleep as sleep
import curses
from futaam.interfaces import ARGS
from futaam.interfaces.common import *
import wikipedia
import lxml.html
#ncurses doesn't resize properly for god knows why
#See http://bugs.python.org/issue2675
os.environ['LINES'] = 'Wow Wow'
os.environ['COLUMNS'] = 'just living in the futabase'
del os.environ['LINES']
del os.environ['COLUMNS']

locale.setlocale(locale.LC_ALL,"")
colors = utils.colors()
ANN = utils.ANNWrapper()
vndb = utils.VNDB('Futaam', '0.1')

class if_ncurses(object):
	##These functions must come first
	def get_terminal_size(self, fd=1):
	    """
	    Returns height and width of current terminal. First tries to get
	    size via termios.TIOCGWINSZ, then from environment. Defaults to 25
	    lines x 80 columns if both methods fail.
	    :param fd: file descriptor (default: 1=stdout)
	    """
	    try:
	        import fcntl, termios, struct
	        hw = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
	    except:
	        try:
	            hw = (os.environ['LINES'], os.environ['COLUMNS'])
	        except:  
	            hw = (25, 80)
	 
	    return hw

	def get_terminal_height(self, fd=1):
	    """
	    Returns height of terminal if it is a tty, 999 otherwise
	    :param fd: file descriptor (default: 1=stdout)
	    """
	    if os.isatty(fd):
	        height = self.get_terminal_size(fd)[0]
	    else:
	        height = 999
	 
	    return height
 
	def get_terminal_width(self, fd=1):
	    """
	    Returns width of terminal if it is a tty, 999 otherwise
	 
	    :param fd: file descriptor (default: 1=stdout)
	    """
	    if os.isatty(fd):
	        width = self.get_terminal_size(fd)[1]
	    else:
	        width = 999
	 
	    return width

	def __init__(self, argv):
		self.synopsis = ''
		self.curitem = 0

		self.confpath = os.path.join(os.getenv('USERPROFILE') or os.getenv('HOME'), '.futaam')
		if os.path.exists(self.confpath):
			f = open(self.confpath, 'r')
			self.confs = json.load(f)
			f.close()
		else:
			self.confs = {}

		# gather arguments
		self.host = ''
		self.port = 8500
		i = 0
		self.password = ''
		self.username = ''
		self.hooks = []

		self.dbfile = ARGS.database
		if ARGS.host:
			self.host = ARGS.host
		if ARGS.password:
			self.password = ARGS.password
		if ARGS.username:
			self.username = ARGS.username
		if ARGS.port:
			self.port = ARGS.port
		if ARGS.hooks:
			self.hooks = ARGS.hooks

		if len(self.dbfile) == 0 and self.host == '':
			print((colors.fail + 'No database file specified' + colors.default))
			sys.exit(1)

		if self.host == '':
			self.dbs = []
			for fn in self.dbfile:
				self.dbs.append(parser.Parser(fn, hooks=self.hooks))
			self.currentdb = 0
		else:
			if self.username == '':
				if 'default.user' in self.confs:
					print(('[' + colors.blue + 'info' + colors.default +'] using default user'))
					self.username = self.confs['default.user']
				else:
					self.username = eval(input('Username for \'' + self.host + '\': '))
			if 'default.password' in self.confs:
				print(('[' + colors.blue + 'info' + colors.default +'] using default password'))
				self.password = self.confs['default.password']
			else:
				self.password = getpass.getpass('Password for ' + self.username + '@' + self.host + ': ')
			self.dbs = []
			self.dbs.append(parser.Parser(host=self.host, port=self.port, username=self.username, password=self.password, hooks=self.hooks))
			self.currentdb = 0

		self.showing = []
		self.range_min = 0
		self.range_max = self.get_terminal_height()
		self.screen = curses.initscr()
		self.screen.keypad(1)
		curses.cbreak()
		curses.noecho()
		curses.curs_set(0)
		curses.start_color()
		curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK) 
		curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK) 
		curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK) 
		curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)
		curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)

		#self.footer = '[Q]uit / [D]elete / [E]dit / [A]dd / [S]ynopsis / [I]mage'
		self.footer = '[Q]uit / [H]elp'
		self.f2 = self.footer

		ANNInitRet = ANN.init()
		if ANNInitRet == 0:
			pass
		elif ANNInitRet == 1:
			print((self.alert('Updating metadata...')))
			ANN.fetch_report(50)
		elif ANNInitRet == 2:
			print((self.alert('Updating ANN metadata cache for the first time...')))
			ANN.fetch_report('all')

		self.redraw()
		self.drawitems()
		while True:
			try:
				x = self.screen.getch()
			except:
				curses.nocbreak()
				curses.echo()
				curses.curs_set(1)
				curses.endwin()
			
			if x == curses.KEY_RESIZE:
				self.showing = []
				self.range_min = 0
				self.range_max = 0
				self.redraw()
				self.drawitems()
				if self.synopsis:
					self.drawSynopsis()
				continue

			if x == ord('q') or x == ord('Q') or x == 27:
				curses.nocbreak()
				curses.echo()
				curses.curs_set(1)
				curses.endwin()
				print((colors.green + 'Bye bye~' + colors.default))
				sys.stdout.flush()
				os._exit(0)
			if x == ord('h') or x == ord('H'):
				if self.get_terminal_height() < 13:
					self.alert('Screen too small')
				else:
					self.redraw(True)
					self.screen.addstr(2, 1, '[Q]uit', curses.color_pair(4))
					self.screen.addstr(3, 1, '[D]elete', curses.color_pair(4))
					self.screen.addstr(4, 1, '[E]dit', curses.color_pair(4))
					self.screen.addstr(5, 1, '[A]dd', curses.color_pair(4))
					self.screen.addstr(6, 1, '[S]ynopsis', curses.color_pair(4))
					self.screen.addstr(7, 1, '[I]mage', curses.color_pair(4))
					#purposefully skip one
					self.screen.addstr(9, 1, '[F5] Move highlighted entry up', curses.color_pair(4))
					self.screen.addstr(10, 1, '[F6] Move highlighted entry down', curses.color_pair(4))

					self.screen.addstr(self.get_terminal_height() - 2, 1, 'Press any key to go back', curses.color_pair(4))
					self.screen.getch()

				self.redraw()
				self.drawitems()
			elif x == ord('S') or x == ord('s'):
				self.drawinfo()
				continue
			elif x == ord('a') or x == ord('A'):
				self.addEntry()
			elif x == ord('d') or x == ord('D'):
				for entry in self.dbs[self.currentdb].dictionary['items']:
					if entry['id'] == self.curitem:
						self.dbs[self.currentdb].dictionary['items'].remove(entry)
						self.dbs[self.currentdb].dictionary['count'] -= 1
						break
				else:
					continue

				##### REBUILD IDS #####
				for x in range(0, self.dbs[self.currentdb].dictionary['count']):
					self.dbs[self.currentdb].dictionary['items'][x]['id'] = x
				#######################
				self.dbs[self.currentdb].save()
				self.redraw()
				self.drawitems()
			elif x == ord('e') or x == ord('E'):
				self.edit()
			elif x == ord('i') or x == ord('I'):
				self.sI()
			elif x == 258: #DOWN
				self.synopsis = ''
				if len(self.dbs[self.currentdb].dictionary['items'])-1 == self.curitem:
					continue
				self.curitem += 1
				self.redraw()
				self.drawitems()
			elif x == 259: #UP
				self.synopsis = ''
				if self.curitem == 0:
					continue
				self.curitem -= 1
				self.redraw()
				self.drawitems(direction=1)
			elif x == 338:
				size = self.get_terminal_size()
				itemsCount = len(self.dbs[self.currentdb].dictionary['items'])-1

				page = size[0] - 4

				target = self.curitem + page - 1

				if target >= itemsCount:
					target = itemsCount

				self.curitem = target
				self.redraw()
				self.drawitems()
			elif x == 339:
				size = self.get_terminal_size()
				itemsCount = len(self.dbs[self.currentdb].dictionary['items'])-1

				page = size[0] - 4

				target = self.curitem - page + 1

				if target <= 0:
					target = 0

				self.curitem = target
				self.redraw()
				self.drawitems()
			elif x == curses.KEY_F5:
				#Move up
				if self.curitem == 0:
					continue

				self.dbs[self.currentdb].dictionary['items'][self.curitem]['id'] = self.curitem - 1
				self.dbs[self.currentdb].dictionary['items'][self.curitem - 1]['id'] = self.curitem
				self.dbs[self.currentdb].dictionary['items'] = sorted(self.dbs[self.currentdb].dictionary['items'], key=lambda x: x['id'])
				self.dbs[self.currentdb].save()

				self.showing[self.curitem - self.range_min]['id'] = self.curitem - 1
				self.showing[(self.curitem - self.range_min) - 1]['id'] = self.curitem
				self.showing = sorted(self.showing, key=lambda x: x['id'])

				self.curitem = self.curitem - 1
				self.redraw()
				self.drawitems()
			elif x == curses.KEY_F6:
				#Move down
				if self.curitem >= len(self.dbs[self.currentdb].dictionary['items']) -1:
					continue

				self.dbs[self.currentdb].dictionary['items'][self.curitem]['id'] = self.curitem + 1
				self.dbs[self.currentdb].dictionary['items'][self.curitem + 1]['id'] = self.curitem
				self.dbs[self.currentdb].dictionary['items'] = sorted(self.dbs[self.currentdb].dictionary['items'], key=lambda x: x['id'])
				self.dbs[self.currentdb].save()

				self.showing[self.curitem - self.range_min]['id'] = self.curitem + 1
				self.showing[(self.curitem - self.range_min) + 1]['id'] = self.curitem
				self.showing = sorted(self.showing, key=lambda x: x['id'])

				self.curitem = self.curitem + 1
				self.redraw()
				self.drawitems()
			else:
				pass
				#self.screen.addstr(10, 10, str(x))		

	def addEntry(self):

		self.redraw(True)
		self.screen.addstr(2, 2, 'Press A for anime')
		self.screen.addstr(3, 2, 'Press M for manga')
		self.screen.addstr(4, 2, 'Press V for visual novel')
		self.screen.addstr(5, 2, 'Press C to cancel')
		x = 0
		while (x in [ord('a'), ord('m'), ord('A'), ord('M'), ord('c'), ord('C'), ord('v'), ord('V')]) == False:
			x = self.screen.getch()
		if x in [ord('c'), ord('C')]:
			self.redraw()
			self.drawitems()
			return
		elif x in [ord('a'), ord('A')]:
			t = 'anime'
		elif x in [ord('M'), ord('m')]:
			t = 'manga'
		elif x in [ord('v'), ord('V')]:
			t = 'vn'

		self.redraw(True)
		name = self.prompt('Name: ', 2)
		if t in ['anime', 'manga']:
			searchResults = ANN.search(name, t)
		elif t == 'vn':
			searchResults = vndb.get('vn', 'basic,details', '(title~"' + name + '")', '')['items']
		if len(searchResults) == 0:
			self.alert(t[0].upper() + t[1:].lower() + ' not found on ANN :\\') #this will be better handled on the future
			self.redraw()
			self.drawitems()
			return
		i = 0
		for x in searchResults:
			searchResults[i]['index'] = i
			searchResults[i]['am'] = t
			i += 1
		self.footer = '[ENTER] Choose / [C] Cancel'
		self.redraw()
		self.scuritem = 0
		self.drawSearch(searchResults)
		while True:
			x = self.screen.getch()
			if x == 258: #DOWN
				if len(searchResults)-1 == self.scuritem:
					continue
				self.scuritem += 1
				self.redraw()
				self.drawSearch(searchResults)
			elif x == 259: #UP
				if self.scuritem == 0:
					continue
				self.scuritem -= 1
				self.redraw()
				self.drawSearch(searchResults)
			elif x == ord('c') or x == ord('C'):
				self.footer = self.f2
				self.redraw()
				self.drawitems()
				return
			elif x == 10:
				selected = searchResults[self.scuritem]
				genre = ''
				if t in ['anime', 'manga']:
					deep = ANN.details(selected['id'], t)
					g = ''
					for genre in deep['genres']:
						g = g + genre + '/'
					genre = g[:-1]
				elif t == 'vn':
					deep = deep = vndb.get('vn', 'basic,details', '(id='+ str(selected['id']) + ')', '')['items'][0]
				title = deep['title']
				self.redraw(True)
				self.screen.addstr(2, 2, '[Status]', curses.A_BOLD)
				self.screen.addstr(3, 2, '[W] - ' + utils.translated_status[t]['w'])
				self.screen.addstr(4, 2, '[C] - ' + utils.translated_status[t]['c'])
				self.screen.addstr(5, 2, '[Q] - ' + utils.translated_status[t]['q'])
				self.screen.addstr(6, 2, '[H] - ' + utils.translated_status[t]['h'])
				self.screen.addstr(7, 2, '[D] - ' + utils.translated_status[t]['d'])
				x = ''
				while (x.lower() in ['w', 'c', 'q', 'h', 'd']) == False:
					x = self.screen.getch()
					if x > 256:
						continue
					x = chr(x)
				if x.lower() == 'w':
					if t == 'anime':
						lastEp = str(selected['episodes'])
					elif t == 'manga':
						lastEp = str(selected['chapters'])
					else:
						lastEp = ''
				elif x.lower() == 'q':
					lastEp = ''
					pass
				else:
					if t == 'anime':
						lastEp = self.prompt('<Last episode watched> ', 8).replace('\n', '')
					elif t == 'manga':
						lastEp = self.prompt('<Last chapter read> ', 9).replace('\n', '')
					else:
						lastEp = ''
				obs = self.prompt('<Observations> ', 10).replace('\n', '')

				try:
					self.dbs[self.currentdb].dictionary['count'] += 1
				except:
					self.dbs[self.currentdb].dictionary['count'] = 1
				self.dbs[self.currentdb].dictionary['items'].append({'id': self.dbs[self.currentdb].dictionary['count'], 'type': t, 'aid': selected['id'], 'name': utils.HTMLEntitiesToUnicode(utils.remove_html_tags(title)), 'genre': utils.HTMLEntitiesToUnicode(utils.remove_html_tags(genre)), 'status': x.lower(), 'lastwatched': lastEp, 'obs': obs})
				for x in range(0, self.dbs[self.currentdb].dictionary['count']):
					self.dbs[self.currentdb].dictionary['items'][x]['id'] = x	
				self.dbs[self.currentdb].save()
				self.screen.addstr(11, 2, 'Entry added!', curses.color_pair(3) + curses.A_REVERSE)
				self.screen.refresh()
				sleep(2)
				self.footer = self.f2
				self.redraw()
				self.drawitems()
				return
	def alert(self, s, time=2):
		terminalsize = self.get_terminal_size()
		self.redraw(True)
		x_m = terminalsize[0] / 2
		x_y = (terminalsize[1] / 2) - (len(s) / 2)

		self.screen.addstr(x_m-1, x_y-1, ' ' * (len(s) + 2), curses.color_pair(1) + curses.A_REVERSE)
		self.screen.addstr(x_m, x_y-1, ' ', curses.color_pair(1) + curses.A_REVERSE)
		self.screen.addstr(x_m, x_y, s, curses.color_pair(1))
		self.screen.addstr(x_m, x_y+len(s), ' ', curses.color_pair(1) + curses.A_REVERSE)
		self.screen.addstr(x_m+1, x_y-1, ' ' * (len(s) + 2), curses.color_pair(1) + curses.A_REVERSE)

		self.screen.refresh()
		sleep(time)
	def edit(self):
		terminalsize = self.get_terminal_size()
		entry = self.dbs[self.currentdb].dictionary['items'][self.curitem]
		self.redraw()
		self.drawitems(True)

		changefields = [{'dbentry': 'name', 'prompt': 'Title: '}, {'dbentry': 'genre', 'prompt': 'Genre: '}, {'dbentry': 'status', 'prompt': 'Status: '}, {'dbentry': 'lastwatched', 'prompt': 'Last watched: '}, {'dbentry': 'obs', 'prompt': 'Observations: '}]

		#Screen size check
		for field in changefields:
			if (len(self.dbs[self.currentdb].dictionary['items'][self.curitem][field['dbentry']]) + len(field['prompt']) + 27) > terminalsize[1]:
				self.alert('Screen too small')
				self.redraw()
				self.drawitems()
				return

		t = 1
		for field in changefields:
			if field['dbentry'] == 'status':
				self.screen.addstr(t, 27, 'Status [W/C/Q/H/D]')
				x = ''
				while (x.lower() in ['w', 'c', 'q', 'h', 'd']) == False:
					x = self.screen.getch()
					if x > 256:
						continue
					x = chr(x)
				self.dbs[self.currentdb].dictionary['items'][self.curitem]['status'] = x.lower()
				t += 1
				continue
			self.dbs[self.currentdb].dictionary['items'][self.curitem][field['dbentry']] = self.prompt(field['prompt'], t, 27, entry[field['dbentry']])
			t += 1
		self.screen.addstr(t+1, 27, 'Entry edited!', curses.color_pair(3) + curses.A_REVERSE)
		self.screen.refresh()
		sleep(2)
		self.dbs[self.currentdb].save()
		self.redraw()
		self.drawitems()

	def prompt(self, p, line, y=2, default=''):
		terminalsize = self.get_terminal_size()
		curses.curs_set(1)
		self.screen.addstr(line, y, p, curses.A_BOLD)
		self.screen.refresh()
		self.screen.addstr(line, len(p) + y, ' '*15, curses.A_REVERSE)
		ret = default
		x = 0
		w = len(p) + y
		if default != '':
			self.screen.addstr(line, w, default, curses.A_REVERSE)
			w += len(default)

		while x != 10:
			x = self.screen.getch()
			if x == 263: #backspace
				if w <= len(p) + y:
					continue
				self.screen.addstr(line, w-1, ' ', curses.A_REVERSE)
				self.screen.addstr(line, w-1, '', curses.A_REVERSE)
				w -= 1
				ret = ret[:-1]
				continue
			if w > terminalsize[1]-5:
				continue
			try:
				self.screen.addstr(line, w, chr(x), curses.A_REVERSE)
			except:
				continue
			w += 1
			ret += chr(x)
		ret = ret.replace('\n', '')
		curses.curs_set(0)
		return ret

	def drawSearch(self, searchResults):
		terminalsize = self.get_terminal_size()
		if terminalsize[0] < 12 or terminalsize[1] < 46:
			self.screen.keypad(0)
			curses.endwin()
			print((colors.fail + '\nScreen too small :C' + colors.default))
			sys.exit(1)
		i = 0
		y = 1
		x = 2
		if self.scuritem > (terminalsize[0]-5):
			showing = searchResults[scuritem-terminalsize[0]+5:self.scuritem+1]
		else:
			showing = searchResults[:terminalsize[0]-4]
		for entry in showing:
			if len(entry['title']) >= 23:
				name = entry['title'][:20] + '...'
			else:
				name = entry['title']
			if entry['index'] == self.scuritem:
				bold = curses.A_REVERSE
				if entry['am'] == 'anime':
					fields = {'Title: ': entry['title'], 'Type: ': entry['type'], 'Episodes: ': str(entry['episodes']), 'Status: ': entry['status']}
				elif entry['am'] == 'manga':
					fields = {'Title: ': entry['title'], 'Type: ': entry['type'], 'Chapters: ': str(entry['chapters']), 'Status: ': entry['status']}
				elif entry['am'] == 'vn':
					fields = {'Title: ': entry['title'], 'Platforms: ': '/'.join(entry['platforms']), 'Released: ': entry['released'], 'Languages: ': '/'.join(entry['languages'])}

				t = 1
				for field in fields:
					if fields[field] == None: fields[field] = ''
					self.screen.addstr(t, 27, field, curses.A_BOLD)
					sizeleft = int(terminalsize[1]) - int(len(field) + len(fields[field])) - 28
					if sizeleft <= 3:
						self.screen.addstr(t, 27 + len(field), fields[field][:sizeleft-3].encode('utf-8') + '...')
						t += 1
						continue
					fix = ' ' * sizeleft
					self.screen.addstr(t, 27 + len(field), fields[field].encode('utf-8') + fix)
					t += 1
				s = 27
				l = t + 1
				workwidth = terminalsize[1] - s-1
				self.screen.addstr(l, s, 'Synopsis: ', curses.A_BOLD)
				skey = 'synopsis'
				if entry['am'] == 'vn': skey = 'description'
				if len(entry[skey]) < workwidth:
					self.screen.addstr(l, s + len('Synopsis: '), entry[skey])
				else:
					self.screen.addstr(l, s + len('Synopsis: '), utils.HTMLEntitiesToUnicode(entry[skey][:workwidth-len('Synopsis: ')]).encode('utf-8'))
					t = workwidth-len('Synopsis: ')
					while len(entry[skey][t:t+workwidth]) != 0:
						l += 1
						if l >= terminalsize[0]-5:
							self.screen.addstr(l, s, utils.HTMLEntitiesToUnicode(utils.remove_html_tags(entry[skey][t:t+workwidth-3].replace('\n', '').replace('\r', '') + '...')).encode('utf-8'))
							break
						self.screen.addstr(l, s, utils.HTMLEntitiesToUnicode(utils.remove_html_tags(entry[skey][t:t+workwidth].replace('\n', '').replace('\r', ''))).encode('utf-8'))
						t += workwidth				
			else:
				bold = 0

			name = name.encode('utf-8')
			self.screen.addstr(x, y, name, bold)

			x += 1
			i += 1		

	def redraw(self, noxtra=False):
		terminalsize = self.get_terminal_size()
		self.screen.clear()
		self.screen.border(0)
		self.screen.addstr(0, 2, self.dbs[self.currentdb].dictionary['name'] + ' - ' + self.dbs[self.currentdb].dictionary['description'], curses.color_pair(1))
		if noxtra == False:
			for line in range(1, terminalsize[0]-1):
				self.screen.addstr(line, 25, '│'.encode('utf-8'))

			self.screen.addstr(terminalsize[0]-2, 1, self.footer)

	def drawitems(self, noSidePanel=False, direction=0):
		terminalsize = self.get_terminal_size()
		if terminalsize[0] < 12 or terminalsize[1] < 46:
			self.screen.keypad(0)
			curses.endwin()
			print((colors.fail + '\nScreen too small :C' + colors.default))
			sys.exit(1)
		i = 0
		y = 1
		x = 2
		#if self.curitem > (terminalsize[0]-5):
		#	showing = self.dbs[self.currentdb].dictionary['items'][self.curitem-terminalsize[0]+5:self.curitem+1]
		#else:
		#	showing = self.dbs[self.currentdb].dictionary['items'][:terminalsize[0]-4]

		##self.showing
		for entry in self.showing:
			if entry['id'] == self.curitem:
				#it's on the list, don't do anything
				break
		else:
			if self.curitem > (terminalsize[0]-5):
				if direction == 0:
					self.showing = self.dbs[self.currentdb].dictionary['items'][self.curitem-terminalsize[0]+5:self.curitem+1]
					self.range_min = self.curitem-terminalsize[0]+5
					self.range_max = self.curitem+1
				elif direction == 1: #UP
					self.showing = self.dbs[self.currentdb].dictionary['items'][self.curitem:terminalsize[0]+self.curitem-5]
					self.range_min = self.curitem
					self.range_max = terminalsize[0]+self.curitem-5
			else:
				self.showing = self.dbs[self.currentdb].dictionary['items'][:terminalsize[0]-4]
				self.range_min = 0
				self.range_max = terminalsize[0]-4


		for entry in self.showing:
			if len(entry['name']) >= 23:
				name = entry['name'][:20] + '...'
			else:
				name = entry['name']
			if entry['id'] == self.curitem:
				bold = curses.A_REVERSE
				if noSidePanel == False:
					if entry['type'] == 'anime':
						fields = (('Title: ', entry['name']), ('Genre: ', entry['genre']), ('Status: ', translated_status[entry['type'].lower()][entry['status'].lower()]), ('Last watched: ', entry['lastwatched']), ('Observations: ', entry['obs']))
					elif entry['type'] == 'manga':
						fields = (('Title: ', entry['name']), ('Genre: ', entry['genre']), ('Status: ', translated_status[entry['type'].lower()][entry['status'].lower()]), ('Last chapter/volume read: ', entry['lastwatched']), ('Observations: ', entry['obs']))
					elif entry['type'] == 'vn':
						fields = (('Title: ', entry['name']), ('Status: ', translated_status[entry['type'].lower()][entry['status'].lower()]), ('Observations: ', entry['obs']))
					t = 1
					out = {'anime': 'Anime', 'manga': 'Manga', 'vn': 'VN'}[entry['type']]
					self.screen.addstr(terminalsize[0]-1, terminalsize[1]-len(out)-1, out, {'anime': curses.color_pair(3), 'manga': curses.color_pair(2), 'vn': curses.color_pair(5)}[entry['type']] + curses.A_REVERSE)
					del out
					for field in fields:
						self.screen.addstr(t, 27, field[0], curses.A_BOLD)
						if isinstance(field[1], str):
							showstr = field[1]
							sizeleft = int(terminalsize[1]) - int(len(str(field[0])) + len(field[1])) - 28
						else:
							showstr = str(field[1])
							sizeleft = int(terminalsize[1]) - int(len(str(field[0])) + len(str(field[1]))) - 28
						if sizeleft <= 3:
							self.screen.addstr(t, 27 + len(field[0]), field[1][:sizeleft-3].encode('utf-8') + '...')
							t += 1
							continue
						fix = ' ' * sizeleft
						self.screen.addstr(t, 27 + len(field[0]), showstr.encode('utf-8') + fix.encode('utf-8'))
						t += 1
					if entry['type'] in ['anime', 'manga']: #what ANN handles
						if entry['aid'] in ANN.caches['ANN_' + entry['type'] + '_cache']:
							self.synopsis = ANN.details(entry['aid'], entry['type'])['synopsis']
							self.drawSynopsis()
			else:
				bold = 0

			name = name.encode('utf-8')
			if entry['status'].lower() == 'w':
				self.screen.addstr(x, y, name, curses.color_pair(3) + bold)
			elif entry['status'].lower() == 'd':
				self.screen.addstr(x, y, name, curses.color_pair(1) + bold)
			elif entry['status'].lower() == 'c':
				self.screen.addstr(x, y, name, curses.color_pair(2) + bold)
			elif entry['status'].lower() == 'h':
				self.screen.addstr(x, y, name, curses.color_pair(4) + bold)
			elif entry['status'].lower() == 'q':
				self.screen.addstr(x, y, name, curses.color_pair(5) + bold)

			x += 1
			i += 1

	def sI(self):		
		entry = self.dbs[self.currentdb].dictionary['items'][self.curitem]
		if entry.get('aid') != None:
			try:
				self.screen.addstr(self.get_terminal_height()-1, 1, 'Fetching URL... Please wait', curses.color_pair(5))
				self.screen.refresh()
				if entry['type'] in ['anime', 'manga']:
					info = ANN.details(entry['aid'], entry['type'])
				elif entry['type'] == 'vn':
					info = vndb.get('vn', 'basic,details', '(id='+ str(entry['aid']) + ')', '')['items'][0]
				else: return
				self.screen.border()
				self.redraw()
				self.drawitems()
			except urllib.error.HTTPError as info:
				self.alert('Error: ' + str(info), 2)
				self.redraw()
				self.drawitems()
				return
			self.screen.addstr(self.get_terminal_height()-1, 1, 'Fetching image... Please wait', curses.color_pair(5))
			self.screen.refresh()

			try:
				wiki_page = wikipedia.page(info['title'])
				parsed = lxml.html.document_fromstring(wiki_page.html().encode('utf8'))
				## libxml2 can shit up the terminal
				self.screen.refresh()
				self.screen.border()
				self.redraw()
				self.drawitems()
				self.screen.addstr(self.get_terminal_height()-1, 1, 'Fetching image... Please wait', curses.color_pair(5))
				##
				img = parsed.xpath('//table[@class="infobox"]//img[1]/@src')[0].getContent()
			except:
				img = ''
			if img.startswith('//'): img = 'http:' + img
			if img != '':
				utils.showImage(img)
			else:
				utils.showImage(info['image' + {'anime': '_url', 'manga': '_url', 'vn': ''}[entry['type']]])
			self.screen.border()
			self.screen.addstr(0, 2, self.dbs[self.currentdb].dictionary['name'] + ' - ' + self.dbs[self.currentdb].dictionary['description'], curses.color_pair(1))

	def drawSynopsis(self):
		terminalsize = self.get_terminal_size()
		entry = self.dbs[self.currentdb].dictionary['items'][self.curitem]
		s = 27
		l = 7 if entry['type'] in ['anime', 'manga'] else 5 if entry['type'] == 'vn' else 7

		workwidth = terminalsize[1] - s-1
		n = 0
		noHTML = lambda x: utils.HTMLEntitiesToUnicode(utils.remove_html_tags(x))

		synopsis = self.synopsis

		self.screen.addstr(l, s, 'Synopsis: ', curses.A_BOLD)
		if len(synopsis) < workwidth:
			self.screen.addstr(l, s + len('Synopsis: '), synopsis.encode('utf8'))
		else:
			t = workwidth-len('Synopsis: ')
			pos = s + len('Synopsis: ')
			for i, word in enumerate(synopsis.split()):
				newLine = False
				if word.find('\n') != -1:
					newLine = True
					word = word.replace('\n', '')
				if pos+len(word) >= terminalsize[1]:
					opos = pos
					pos = s
					l += 1
					if l >= terminalsize[0]-2:
						if i < len(synopsis.split()):
							if terminalsize[1]-opos-1 > 0:
								self.screen.addstr(l-1, opos, noHTML(word[:terminalsize[1]-opos-1]).encode('utf8'))
							self.screen.addstr(l-1, terminalsize[1]-4, '...')
						break
				self.screen.addstr(l, pos, noHTML(word).encode('utf8'))
				pos += len(word) + 1
				if newLine:
					l += 1
					pos = s

	def drawinfo(self):
		terminalsize = self.get_terminal_size()
		entry = self.dbs[self.currentdb].dictionary['items'][self.curitem]
		s = 27
		l = 7 if entry['type'] in ['anime', 'manga'] else 5 if entry['type'] == 'vn' else 7

		workwidth = terminalsize[1] - s-1
		n = 0
		noHTML = lambda x: utils.HTMLEntitiesToUnicode(utils.remove_html_tags(x))
		
		if entry.get('aid') != None:
			try:
				self.screen.addstr(self.get_terminal_height()-1, 1, 'Fetching synopsis... Please wait', curses.color_pair(5))
				self.screen.refresh()
				if entry['type'] in ['anime', 'manga']:
					info = ANN.details(entry['aid'], entry['type'])
				elif entry['type'] == 'vn':
					info = vndb.get('vn', 'basic,details', '(id='+ str(entry['aid']) + ')', '')['items'][0]
					info['synopsis'] = info['description']
				else:
					return
				info['synopsis'] = utils.remove_html_tags(info['synopsis'])
				self.screen.border()
				out = {'anime': 'Anime', 'manga': 'Manga', 'vn': 'VN'}[entry['type']]
				self.screen.addstr(terminalsize[0]-1, terminalsize[1]-len(out)-1, out, {'anime': curses.color_pair(3), 'manga': curses.color_pair(2), 'vn': curses.color_pair(5)}[entry['type']] + curses.A_REVERSE)
				del out
				self.screen.addstr(0, 2, self.dbs[self.currentdb].dictionary['name'] + ' - ' + self.dbs[self.currentdb].dictionary['description'], curses.color_pair(1))
			except urllib.error.HTTPError as info:
				self.screen.addstr(l, s, 'Error: ' + str(info), curses.color_pair(1) + curses.A_BOLD)
				return
			self.synopsis = info['synopsis']
			self.drawSynopsis()


def main(argv, version):
	try:
		obj = if_ncurses(argv)
	except:
		print((sys.exc_info()[0]))
		curses.endwin()
		raise

def print_help():
	return 'No particular arguments for this interface... Sorry to disappoint'
