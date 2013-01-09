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
from interfaces.common import *
import os
import sys
import ConfigParser
import datetime

PS1 = '[%N]> '
configfile = os.path.join(os.getenv('USERPROFILE') or os.getenv('HOME'), '.futaam')
confs = ConfigParser.RawConfigParser()
if os.path.exists(configfile): confs.read(configfile)
try:
	PS1 = confs.get('Futaam', 'PS1')
except:
	PS1 = '[%green%%N%default%]> '
if PS1 == None: PS1 = '[%green%%N%default%]> '
if PS1[-1:] != ' ': PS1 += ' '

colors = utils.colors()
def main(argv):
	global PS1
	global configfile
	global confs
	#GLOBAL VARIABLES ARRRRRGH

	dbfile = []
	for x in argv:
		if os.path.exists(x):
			dbfile.append(x)
		elif x == '-c' or x == '--create':
			print colors.header + 'Creating database' + colors.default + '\n'
			filename = raw_input('Path to new file> ')
			if filename == '':
				i = 0
				while True:
					if i == 0:
						filename = 'unnamed.ft'
					else:
						filename = 'unnamed.' + str(i) + '.ft'
					if os.path.exists(filename):
						i += 1
						continue
					else:
						break
			if os.path.exists(filename):
				print colors.fail + 'File exists' + colors.default
				sys.exit(1)
			dbtype = raw_input('Type [json/pickle] [json]> ').lower()
			if dbtype == '': dbtype = 'json'
			title = raw_input('Database name> ')
			if title == '': title = 'Unnamed'
			description = raw_input('Description of your database> ') #No need to have a default one
			parser.createDB(filename, dbtype, title, description)
			print '\n\n' + colors.green + 'Database created' + colors.default
			sys.exit(0)
	if len(dbfile) == 0:
		print colors.fail + 'No database specified' + colors.default
		print 'To create a database, use the argument "--create" or "-c" (no quotes)'
		sys.exit(1)
	dbs = []
	for fn in dbfile:
		dbs.append(parser.Parser(fn))
	currentdb = 0
	print colors.header + dbs[currentdb].dictionary['name'] + colors.default + ' (' + dbs[currentdb].dictionary['description'] + ')'
	print 'Type help for cheat sheet'
	if len(dbs) > 1:
		print 'Type switchdb to change to the next database'
	sys.stdout.write('\n')

	while True:
		try:
			now = datetime.datetime.now()
			ps1_replace = {'%N': dbs[currentdb].dictionary['name'], '%D': dbs[currentdb].dictionary['description'], '%h': now.strftime('%H'), '%m': now.strftime('%M'), chr(37) + 's': now.strftime('%S'), '%blue%': colors.blue, '%green%': colors.green, '%red%': colors.fail, '%orange%': colors.warning, '%purple%': colors.header, '%default%': colors.default}
			ps1_temp = PS1
			ps1_temp = ps1_temp.replace('\%', '%' + chr(5))
			for x in ps1_replace:
				ps1_temp = ps1_temp.replace(x, ps1_replace[x])
			ps1_temp = ps1_temp.replace(chr(5), '')
			cmd = raw_input(ps1_temp + colors.default)
			cmdsplit = cmd.split(' ')
			args = ''
			for x in cmdsplit[1:]:
				args += x + ' '
			args = args[:-1]
		except (EOFError, KeyboardInterrupt):
			print colors.green + 'Bye~' + colors.default
			sys.exit(0)

		if cmdsplit[0].lower() in ['q', 'quit']:
			print colors.green + 'Bye~' + colors.default
			sys.exit(0)
		elif cmdsplit[0].lower() in ['set_ps1', 'sps1']:
			args += ' '
			if confs.sections().__contains__('Futaam') == False:
				confs.add_section('Futaam')
			confs.set('Futaam', 'PS1', args)
			with open(configfile, 'wb') as f:
				confs.write(f)
				f.close()
			PS1 = args
		elif cmdsplit[0].lower() in ['help', 'h']:
			print colors.header + 'Commands' + colors.default
			print '\thelp or h - prints this'
			print '\tquit or q - quits'
			print '\tset_ps1 or sps1 - changes PS1'
			print '\tswitchdb or sdb - changes working database when opened with multiple files'
			print ''
		elif cmdsplit[0].lower() in ['switchdb', 'sdb']:
			try:
				currentdb += 1
				repr(dbs[currentdb])
			except IndexError:
				currentdb = 0
			print 'Current database: ' + colors.header + dbs[currentdb].dictionary['name'] + colors.default + ' (' + dbs[currentdb].dictionary['description'] + ')'
		else:
			print colors.warning + 'Command not recognized' + colors.default
			continue

def help():
	ret = colors.header + 'Help for text interface' + colors.default + '\n'
	ret += colors.header + 'Usage: ' + colors.default + sys.argv[0] + ' [filename] [options]\n\n'
	ret += '\t--create or -c initiates the database creation routine'
	return ret