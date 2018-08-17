import random
import math
import sqlite3
from sqlite3 import Error
import sys,os
import types

def dict_factory(cursor, row):
	d = {}
	for idx, col in enumerate(cursor.description):
		d[col[0]] = row[idx]
	return d


class db():
	def __init__(self):		
		try:
			self.path = os.path.dirname(os.path.abspath(__file__)).replace("\\","/") + "/DND.db"
		except:
			self.path = 'D:/Files/Personal/Code Projects/DND/Python/DND.db'
		self.connection = sqlite3.connect(self.path)
		self.connection.row_factory = dict_factory
	def execute(self, sql_str,sql_args=[]):
		return self.connection.execute(sql_str, sql_args)
	def addTrigger(self, parent_table = '', parent_identifier = '', child_table = '', child_identifier = '', trigger_level=1):
		#adds a trigger to the database
		#define default search fields for each table (searched if identifier is non-numeric
		default_lookup_columns = {
								'races':'race',
								'classes':'class',
								'enhancements':'title',
								'proficiencies':'like tags',
								'spells':'name',
								'traits':'trait'}
		
		if isinstance(parent_identifier, list):
			parents = parent_identifier
		else:
			parents = parent_identifier.split(',')
		
		if isinstance(child_identifier,list):
			children = child_identifier
		else:
			children = child_identifier.split(',')
		if parent_table in default_lookup_columns.keys():
			l_col = default_lookup_columns[parent_table]
			if 'like' in l_col:
				l_col = l_col.replace('like ','')
				similar_search = True
			else:
				similar_search = False
			for parent in parents:
				if not parent.isdigit():
					#set parent equal to the id corresponding to the default lookup value
					r = self.execute('SELECT id FROM {} WHERE {} {}'.format(parent_table,
					l_col, '= "{}"'.format(parent) if not similar_search else ' LIKE "*{}*"'.format(parent)).fetchone()
					parent = r['id']
		if child_table in default_lookup_columns.keys():
			l_col = default_lookup_columns[child_table]
			if 'like' in l_col:
				l_col = l_col.replace('like ','')
				similar_search = True
			else:
				similar_search = False
			for child in children:
				if not child.isdigit():
					#set parent equal to the id corresponding to the default lookup value
					r = self.execute('SELECT id FROM {} WHERE {} {}'.format(child_table,
					l_col, '= "{}"'.format(child) if not similar_search else ' LIKE "*{}*"'.format(child)).fetchone()
					child = r['id']
		for parent in parents:
			self.execute("INSERT INTO triggers (parent_table, parent_id, child_table, child_id, trigger_lvl) VALUES ('{}','{}','{}','{}','{}')".format(
			parent_table, parent, child_table, ','.join(children),trigger_lvl)
					
			
class check():
	def __init__(self, check_id=0):
		if check_id == 0:
			self.formula = 'True'
			self.id = 0
		else:
			r = db().execute("SELECT * FROM checks WHERE id =:id",
			{'id':check_id}).fetchone()
			self.formula = r['formula']
			self.id = r['id']   

class proficiency():
	def __init__(self,prof_type='',tags=[], value=0, prof_id=0):
		if prof_id != 0:
			self.load(prof_id)
		else:
			self.type = prof_type
			self.tags = tags
			self.value = value
			self.id = prof_id
	def load(self,prof_id):
		r = db().execute("SELECT * FROM proficiencies WHERE id=?",[(prof_id)]).fetchone()
		self.type = r['type']
		self.tags = ','.split(r['tags'])
		self.value = r['mod_value']
		self.id = r['id']
	

class attribute:
	def __init__(self, attr_name='unnamed attribute', attr_score=10):
		self.name = attr_name
		self.score = attr_score
	
class skill:
	def __init__(self, skill_name='unnamed skill', 
	skill_attr=None, skill_mods={}):
		self.name = skill_name
		self.attribute = skill_attr
		self.mods = skill_mods
	def getScore(self):
		attr_mod = 0
		if not self.attribute == None:
			attr_mod = int((self.attribute.score - 10)/2)
		misc_mods = 0
		for k in list(self.mods.keys()):
			misc_mods += self.mods[k].value
		return attr_mod + misc_mods
class trait:
	def __init__(self, trait_id=0,trait_name='Unknown Trait',
	description='Undefined trait'):
		self.id = trait_id
		self.name = trait_name
		self.description = description
		self.checks = []
		if trait_id != 0:
			self.load(trait_id)
	def __repr__(self):
		return str({'name':self.name, 
		'description':self.description, 'id':self.id})
	def load(self, trait_obj):
		con = db()
		if isinstance(trait_obj,str):		 
			r = con.execute("SELECT * FROM traits WHERE lower(trait) = lower(?)",
			[trait_obj])
		elif isinstance(trait_obj, (types.IntType,types.LongType)):
			r = con.execute("SELECT * FROM traits WHERE id = ?",[trait_obj])
		record = r.fetchone()
		self.name = record['trait']
		self.description = record['description']
		self.id = record['id']
		 

class modifier:
	def __init__(self, mod_type='attribute',mod_tags=[], mod_value=0, 
	enhancement_id=0):
		self.mod_type = mod_type
		self.value = mod_value
		self.tags = mod_tags
		self.id = enhancement_id
		self.additive = False
	def load(self, enhancement_id):
		if isinstance(enhancement_id,(types.IntType, types.LongType)):
			r = db().execute("SELECT * FROM enhancements Where id = :id",
			{'id':enhancement_id}).fetchone()
			
		self.id = r['id']
		self.type = r['type']
		self.tags = ','.split(r['tags'])
		self.value = r['value']
		self.additive = bool(r['additive'])
	def hasTag(self,tag_name):
		try:
			self.tags.index(tag_name)
			return True
		except:
			return False
			
	def addTag(self,tag_name):
		if not self.hasTag(tag_name):
			self.tags.append(tag_name)
 
	def removeTag(self,tag_name):
		if self.hasTag(tag_name):
			del self.tags[self.tags.index(tag_name)]  
class item:
	def __init__(self, item_name='unnamed item',item_weight=0.0,item_qty=1,item_value=0.0):
		self.name = item_name
		self.weight = item_weight
		self.qty = item_qty
		self.value = item_value
		self.checks = []

class weapon(item):
	def __init__(self, item_name='unnamed item',item_weight=0.0,item_qty=1,
	item_value=0.0,weapon_type='unspecified',base_damage='1d6'):
		super().__init__(item_name,item_weight,item_qty,item_value)
		self.weapon_type = weapon_type
		self.base_damage = base_damage
class wearable(item):
	pass

class consumable(item):
	pass

class spell():
	def __init__(self, spell_name='Unnamed Spell', spell_lvl=0):
		self.name = spell_name
		self.description = ''
		self.id = 0
		self.casting_time = ''
		self.range = ''
		self.components = ''
		self.duration = ''
		self.level = spell_lvl
		self.tags = ''
		self.damage_function = ''
		self.higher_level_effects = ''
		self.checks = []
	def load(self,spell_obj):
		con = db()
		if isinstance(spell_obj,str):		 
			r = con.execute("SELECT * FROM spells WHERE lower(name) = lower(?)",
			[spell_obj])
		elif isinstance(spell_obj, (types.IntType,types.LongType)):
			r = con.execute("SELECT * FROM spells WHERE id = ?",[spell_obj])
		record = r.fetchone()
		self.name = record['name']
		self.description = record['description']
		self.id = record['id']
		self.casting_time = record['casting_time']
		self.range = record['range']
		self.components = record['components']
		self.duration = record['duration']
		self.level = record['level']
		self.tags = record['tags']
		self.damage_function = record['damage_function']
		self.higher_level_effects = record['higher_level_effects']
class spell_slot():
	def __init__(self, slot_level=1,depleted=False):
		self.level = slot_level
		self.depleted = depleted
		self.checks = []

class player_class():
	def __init__(self,class_id=0, class_name='Unknown Class', 
	description='Class has not been set', hit_die='1d6',start_hp=6,
	hp_per_lvl=4, parent = None):
		self.id = class_id
		self.level = 0
		self.name = class_name
		self.description = description
		self.favored_attr = []
		self.hit_die=hit_die
		self.start_hp=start_hp
		self.hp_per_lvl=hp_per_lvl
		self.parent = parent
		self.subclasses = {}		
		self.checks = []
		if class_id != 0 or class_name != 'Unknown Class':
			self.load(class_id if class_id != 0 else class_name)
	def load(self,class_obj):
		con = db()
		if isinstance(class_obj,str):		 
			r = con.execute("SELECT * FROM classes WHERE lower(class) = lower(?)",
			[class_obj])
		elif isinstance(class_obj, (types.IntType,types.LongType)):
			r = con.execute("SELECT * FROM classes WHERE id = ?",[class_obj])
		record = r.fetchone()
		self.name = record['class']
		self.description = record['description']
		self.id = record['id']
		self.hit_die = record['hit_die']
		self.start_hp = record['start_hp']
		self.hp_per_lvl = record['hp_per_lvl']
		if record['favored_attr'] != None:
			self.favored_attr = [str(attr.strip()) for attr in record['favored_attr'].split(',')]
		else:
			self.favored_attr = []
	def subclass(self, rand_select=False):
		r = db().execute("SELECT * FROM classes WHERE parent_id = :p_id",{'p_id':self.id}).fetchall()
		#prompt user for subclass
		if rand_select:
			selection = random.randint(1,len(r))
		else:
			print 'You must now choose a subclass for your character. The parent class is ' + self.name + '. Subclasses are detailed below:'
			for i,row in enumerate(r):
				print '\n--- Option ' + str(i+1) + ' ------------------------'
				print '\t' + row['class'] + ':'
				c_ind, line_break = 0, 40 
				while c_ind < len(row['description']):
					next_ind = row['description'].rfind(' ',c_ind,c_ind+line_break)
					if next_ind == -1:
						next_ind = len(row['description'])
					print '\t' + row['description'][c_ind:next_ind]
					c_ind = next_ind + 1
			selection = -1
			while selection < 1 or selection > len(r):
				try:
					selection = int(input('Select an option by typing it\'s number: '))
				except:
					selection = -1
		cls = player_class()
		cls.load(r[selection-1]['id'])
		cls.level = self.level
		self.subclasses[cls.name] = cls
	def level_up(self):
		self.level += 1
		for (nm,cls) in self.subclasses.items():
			cls.level += 1  
class race():
	def __init__(self, race_name="No Race", parent = None, race_id = 0):
		self.parent = parent
		self.name = race_name
		self.subraces = {}
		self.description = ''
		self.id = race_id
		if race_id != 0 or race_name != 'No Race':
			self.load(race_id if race_id != 0 else str(race_name))
	def load(self, race_identifier):
		con = db()
		if isinstance(race_identifier,str):		
			r = con.execute("SELECT * FROM races WHERE \
			lower(race) = lower(?)",[(race_identifier)])
		elif isinstance(race_identifier, (types.IntType, types.LongType)):
			r = con.execute("SELECT * FROM races WHERE \
			id = ?",[(race_identifier)])			
		record = r.fetchone()
		self.name = record['race']
		self.description = record['description']
		self.id = record['id']
		self.subraces = {}
	def subrace(self,rand_select=False):
		r = db().execute("SELECT * FROM races WHERE parent_id = :p_id", \
		{'p_id':self.id}).fetchall()
		if rand_select:
			selection = random.randint(1,len(r))
		else:
		#prompt user for subclass
			print \
			'You must now choose a sub-race for your character. The parent race is '\
			+ self.name + '. Sub-race variants are detailed below:'
			for i,row in enumerate(r):
				print '\n--- Option ' + str(i+1) + ' ------------------------'
				print '\t' + row['race'] + ':'
				c_ind, line_break = 0, 40 
				while c_ind < len(row['description']):
					next_ind = row['description'].rfind(' ',c_ind,c_ind+line_break)
					if next_ind == -1:
						next_ind = len(row['description'])
					print '\t' + row['description'][c_ind:next_ind]
					c_ind = next_ind + 1
			selection = 0
			while selection < 1 or selection > len(r):
				selection = input('Select an option by typing it\'s number: ')
			print "Selected ID: " + str(r[selection-1]['id'])
		sub_race = race(race_id=r[selection-1]['id'])		   
		self.subraces[sub_race.name] = sub_race
		sub_race.parent = self.parent
		return sub_race
class character:
	def __init__(self, randomize=False, char_name='',char_class=None,
	char_race=None,gender='m'):
		#initialize attributes
		self.rand_select = False
		self.attributes = {}
		self.skills = {}
		self.spells = {}
		self.traits = {}
		self.modifiers = {}
		self.spell_limit = 0
		self.max_hp = 0
		self.hp = 0
		self.temp_hp = 0
		self.attr_assigned = False
		self.gender = gender
		self.spell_slots = [[],[],[],[],[],[],[],[],[],[]]
		self.attribute_points = {'total':0, 'remaining':0}
		self.checks = []
		self.proficiencies = []
		self.triggerMgr = triggerParser(parent=self)
		self.classes = {}
		if not char_class == None and isinstance(char_class,(player_class,str,int,long)):
			self.addClass(char_class)
		elif not randomize:
			self.choose_class()
		
		self.races = {}
		if not char_race == None and isinstance(char_race,(race,str,int,long)):
			self.addRace(char_race)
		elif not randomize:
			self.choose_race()
		if char_name == '':
			self.name = name_generator.getName(False)
		else:
			self.name = char_name
		
		attr_list = ['strength','dexterity','constitution','intelligence',
					 'wisdom','charisma']
		skill_list = [  ['acrobatics','dexterity'],
						['animal handling','wisdom'],
						['arcana','intelligence'],
						['athletics','strength'],
						['deception','charisma'],
						['history','intelligence'],
						['insight','wisdom'],
						['intimidation','charisma'],
						['investigation','intelligence'],
						['medicine','wisdom'],
						['nature','intelligence'],
						['perception','wisdom'],
						['performance','charisma'],
						['persuasion','charisma'],
						['religion','intelligence'],
						['stealth','dexterity'],
						['survival','wisdom']
					]		
		for attr in attr_list:
			self.attributes[attr] = attribute(attr)
		for skl in skill_list:
			self.skills[skl[0]] = skill(skill_name=skl[0],
			skill_attr=self.attributes[skl[1]])
		if randomize:
			self.randomize()
		else:
			print "Would you like to use the default stat rolls?"
			use_def = ''
			while use_def not in ['Y','N']:
				try:
					use_def = raw_input("Y/N: ").upper()[0]
				except:
					use_def = ''
			print "Would you like to auto-assign stat rolls?"
			auto = ''
			while auto not in ['Y','N']:
				try:
					auto = raw_input("Y/N: ").upper()[0]
				except:
					auto = ''
			self.roll_stats(use_standard=(use_def=='Y'),auto_assign=(auto=='Y'))
		self.level_up()
		self.calc_base_hp()
	def randomName(self,use_races=True,race='',tags=[]):
		if race == '' and len(self.races) > 0:
			race = self.races.keys()[random.randint(0,len(self.races))-1].lower()
		self.name = name_generator.getName(use_races,race,self.gender,tags)
	def __str__(self):
		return_str = "="*30 +"\n"
		return_str += 'Name: ' + self.name + "\n"
		return_str += "Level: {}\n".format(self.level())
		return_str += "HP: {}/{}\n".format(self.hp+self.temp_hp,self.max_hp)
		return_str += "="*30 +"\n"
		return_str += " Attributes \n"
		return_str += "="*30 +"\n"
		for attr_name in self.attributes.keys():
			return_str += "   {}\t{}\n".format((attr_name+' '*13)[:13],self.attributes[attr_name].score)
		return_str += "="*30 +"\n"
		return_str += " Races \n"
		return_str += "="*30 +"\n"
		for race_name in self.races.keys():
			return_str += '   ' + race_name + "\n"
			for sub_race_name in self.races[race_name].subraces.keys():
				return_str += "      {}\n".format(sub_race_name)
		return_str += "="*30 +"\n"
		return_str += " Classes \n"
		return_str += "="*30 +"\n"
		for class_name in self.classes.keys():
			return_str += '   ' + class_name + "\n"
			for sub_class_name in self.classes[class_name].subclasses.keys():
				return_str += "      {}\n".format(sub_class_name)
		return_str += "="*30 +"\n"
		return_str += " Traits\n"
		return_str += "="*30 +"\n"
		for trait_name in self.traits.keys():
			return_str += "   {}\n".format(trait_name)
		return_str += "="*30 +"\n"
		return_str += " Spells\n"
		return_str += "="*30 +"\n"
		for spell_name in self.spells.keys():
			return_str += "   {}\n".format(spell_name)
		return return_str
	def calc_base_hp(self):
		#get the hp at level 1 for the character
		self.max_hp
		for cls_name in self.classes.keys():
			c_cls = self.classes[cls_name]
			if c_cls.level > 0:
				self.max_hp = self.calculate('{}+mod.const'.format(c_cls.start_hp))['result']
				self.hp = self.max_hp
				break
		
	def randomize(self):
		con = db()
		self.rand_select = True
		#get random race
		rs = [r_item['id'] for r_item in con.execute("SELECT id from races where parent_id is null")]
		self.races = {}
		self.addRace(rs[random.randint(0,len(rs)-1)])
		#get random class
		rs = [r_item['id'] for r_item in con.execute("SELECT id from classes where parent_id is null")]
		self.classes = {}
		self.addClass(rs[random.randint(0,len(rs)-1)])
		#randomize name
		try:
			self.name = name_generator.getName(race_description=self.races.keys()[0].lower())
		except:
			self.name = name_generator.getName(False)
		self.roll_stats(use_standard=False,auto_assign=True)
	def roll_stats(self, use_standard=True, auto_assign=False):
		score_array = [15,14,13,12,10,8]
		if not use_standard:
			score_array = [self.calculate('3d6/a')['result'] for i in range(0,6)]
		score_array.sort(reverse=True)
		if auto_assign:
			assigned_indices = []
			#get player class
			prim_class = [(cls_obj.level,cls_obj) for cls_name,cls_obj in self.classes.iteritems()]
			prim_class.sort(reverse=True)
			if len(prim_class) > 0:
				prim_class = prim_class[0][1]
			else:
				prim_class = player_class()
			for i,attr_name in enumerate(prim_class.favored_attr):
				self.attributes[attr_name].score = score_array[i]
				assigned_indices.append(i)
			for attr_name in [key for key in self.attributes.keys() if key not in prim_class.favored_attr]:
				c_ind = random.randint(0,len(score_array)-1)
				while c_ind in assigned_indices:
					c_ind = random.randint(0,len(score_array)-1)				
				self.attributes[attr_name].score = score_array[c_ind]
				#print '{} = {}'.format(attr_name,score_array[c_ind])
				assigned_indices.append(c_ind)
		else:
			self.choose_stats(score_array)
	def choose_race(self):
		d = db()
		r = d.execute('Select race, description from races where parent_id is null').fetchall()
		print "=================\n CHOOSE A RACE \n=================\n"
		for r_item in r:
			print ' -- {} ---------------'.format(r_item['race'])
			print "\n  {}\n".format(r_item['description'])
		sel_race = str(raw_input('Select a race from the list above. Type the race name here: '))
		self.addRace(sel_race)
	def choose_class(self):
		d = db()
		r = d.execute('Select class, description from classes where parent_id is null').fetchall()
		print "=================\n CHOOSE A CLASS \n=================\n"
		for r_item in r:
			print ' -- {} ---------------'.format(r_item['class'])
			print "\n {}\n".format(r_item['description'])
			
		sel_class = str(raw_input('Select a class from the list above. Type the class name here: '))
		self.addClass(sel_class)
		
	def choose_stats(self,score_array):
		#allow user to assign stats
		
		#print score array, prompt user for attr score
		for attr_name in [key for key in self.attributes.keys()]:
				print 'Available Scores:'
				print [score for score in score_array]
				c_ind = -1
				while c_ind == -1:
					c_score = int(input('Select a score for {}: '.format(attr_name)))
					try:
						c_ind = score_array.index(c_score)
					except:
						c_ind = -1				
				self.attributes[attr_name].score = score_array[c_ind]
				#print '{} = {}'.format(attr_name,score_array[c_ind])
				del score_array[c_ind]
	def getAttrMod(self, mod_str):
		mod_tag = mod_str.replace('mod.','')
		for attr in list(self.attributes.keys()):
			if attr[0:len(mod_tag)].lower() == mod_tag.lower():
				attr_score_base = self.attributes[attr].score - 10
				return int(attr_score_base/2)
		return None
	def getSkillMod(self, mod_str):
		mod_tag = mod_str.replace('skill.','')
		for skl in list(self.skills.keys()):
			if skl[0:len(mod_tag)].lower() == mod_tag.lower():
				skl_score_base = self.skills[skl].getScore()
				return int(skl_score_base)
		return None
	def addSpell(self, spell_obj):
		if isinstance(spell_obj,spell):
			self.spells[spell_obj.name] = spell_obj
		elif isinstance(spell_obj,(str,types.IntType, types.LongType)):
			spl = spell()
			spl.load(spell_obj)
			self.spells[spl.name] = spl
			spell_obj = self.spells[spl.name]
		self.triggerMgr.getAndProcess(spell_obj.id, 'spells')
		return spell_obj		
		
	def addRace(self, race_obj, process_triggers=True):
		is_added = False
		if isinstance(race_obj,race):
			self.races[race_obj.name] = race_obj
			is_added = True
			r = self.races[race_obj.name] 
		elif isinstance(race_obj, (str,types.IntType, types.LongType)):
			r = race()
			r.load(race_obj)
			self.races[r.name] = r			
			is_added = True
		ret_val = r
		r.parent = self
		if is_added and process_triggers:
			self.triggerMgr.getAndProcess(r.id, 'races')
		return ret_val
	def addClass(self, class_obj, process_triggers=True):
		is_added = False
		calc_lvl1 = (len(self.classes) == 0)
		if isinstance(class_obj,player_class):
			self.classes[class_obj.name] = class_obj
			is_added = True
		elif isinstance(class_obj, (str,types.IntType, types.LongType)):
			cls = player_class()
			cls.load(class_obj)
			self.classes[cls.name] = cls
			is_added = True
		if is_added and process_triggers:
			self.triggerMgr.getAndProcess(cls.id, 'classes')
		if calc_lvl1:
			pass
	def addTrait(self, trait_obj, process_triggers=True):
		is_added = False
		if isinstance(trait_obj,trait):
			self.classes[trait_obj.name] = trait_obj
			is_added = True
		elif isinstance(trait_obj, (str,types.IntType, types.LongType)):
			t = trait()
			t.load(trait_obj)
			self.traits[t.name] = t
			is_added = True
		if is_added and process_triggers:
			self.triggerMgr.getAndProcess(t.id, 'traits')
	def skillCheck(self, mod_str):
		return self.calculate('1d20 + skill.' + mod_str.replace('skill.',''))
	def calculate(self,eval_str):
		#evaluates a calculation string
		#form: a + b - c
		# can include:
		#   - dice roll expressions (1d6/a + 3d8/d)
		#	   {/a = advantage, /d = disadvantage}
		#   - ability modifiers (mod.dex)
		#   - skill checks (skill.acro)
		#   - half level indicator (hf_lvl)
		result = 0
		rl = roller()
		#split the values based on + and -
		prev_ind = 0
		next_mod = 1
		split_str = []
		for i, x in enumerate(eval_str):
			if x == '+':
				split_str.append({'expression':eval_str[prev_ind:i].strip(),'multiplier':next_mod})
				prev_ind = i + 1
				next_mod = 1
			elif x == '-':
				split_str.append({'expression':eval_str[prev_ind:i].strip(),'multiplier':next_mod})
				prev_ind = i + 1
				next_mod = -1
			if i == len(eval_str) - 1:
				split_str.append({'expression':eval_str[prev_ind:].strip(),'multiplier':next_mod})
		#loop through each item and calculate it
		#print split_str
		for i,x in enumerate(split_str):
			eval_val = x['expression'].strip()
			#print eval_val
			add_val = 0
			if eval_val[0:3] == 'mod':
				attr = self.getAttrMod(eval_val)
				add_val = x['multiplier'] * attr
			elif eval_val == 'hf_lvl':
				add_val = x['multiplier'] * int(self.level/2)
			elif eval_val[0:5] == 'skill':
				add_val = x['multiplier'] * self.getSkillMod(eval_val)
			else:
				add_val= x['multiplier'] * rl.roll(eval_val)['value']
			result += add_val
			split_str[i]['value'] = add_val
		return {"result" : result, "split_str": split_str}
	def level_up(self, increase_by=1, use_default=True):
		#increase the player level
		class_list = self.classes.items()
		for i in range(1, increase_by+1):
			#prompt for class
			c_obj = None
			if not use_default:
				while c_obj == None:
					lvl_up_class = str(input("Toward which class would you like \
					to apply this level gain? "))
					
					if lvl_up_class == "":
						c_obj = class_list[0]
					else:
						try:
							c_obj =  self.classes[lvl_up_class.title()]
						except:
							try:
								self.addClass(lvl_up_class.title())
								c_obj = self.classes[lvl_up_class.title()]
								c_obj.level = 0
							except:
								print "No such class found: " + lvl_up_class
			else:
				c_obj = self.classes[self.classes.keys()[0]]
			c_obj.level_up()
			self.triggerMgr.getAndProcess(parent_id=c_obj.id,
			parent_table='classes',level_trigger=c_obj.level)
			if len(c_obj.subclasses) > 0:
				for (nm,cls) in c_obj.subclasses.items():
					self.triggerMgr.getAndProcess(parent_id=cls.id,
						parent_table='classes',level_trigger=cls.level)
	def subclass(self, class_id):
		for (nm,cls) in self.classes.items():
			if cls.id == class_id:
				cls.subclass(self.rand_select)
	def subrace(self, race_id):
		for (nm,rc) in self.races.items():
			if rc.id == race_id:
				s_race = rc.subrace(self.rand_select)
				self.triggerMgr.getAndProcess(s_race.id,'races')
	def addEnhancement(self, mod_obj):
		add_mod = None
		if isinstance(mod_obj, modifier):
			add_mod = mod_obj
		elif isinstance(mod_obj,(types.IntType,types.LongType)):
			add_mod = modifier()
			add_mod.load(mod_obj)
		self.processMod(add_mod)
		return add_mod
	def addProficiency(self, prof_obj):
		add_prof = None
		if isinstance(prof_obj, proficiency):
			add_prof = prof_obj
		elif isinstance(prof_obj,(types.IntType,types.LongType)):
			add_prof = proficiency(prof_id=prof_obj)
			
		self.proficiencies.append(add_prof)
		return add_prof
	def processMod(self, mod_obj):
		if isinstance(mod_obj,modifier):
			if mod_obj.type == 'attribute_points':
				self.attribute_points['total'] += int(mod_obj.value)
				self.attribute_points['remaining'] += int(mod_obj.value)
			elif mod_obj.type == 'spell_limit':
				self.spell_limit += mod_obj.value
			elif mod_obj.type == 'cantrip_limit':
				spl_slot = spell_slot(slot_level=0)
				self.spell_slots[0].append(spl_slot)
			else:
				if mod_obj.additive==True:
					if str(mod_obj.id) in self.modifiers:
						self.modifiers[str(mod_obj.id)].append(mod_obj)
					else:
						self.modifiers[str(mod_obj.id)] = [mod_obj]
				else:
					self.modifiers[str(mod_obj.id)] = [mod_obj]
	def proficiency_mod(self):
		return math.floor(float(self.level()-1)/4)+2
	def level(self):
		ret_val = 0
		for (nm,cls) in self.classes.items():
			ret_val += cls.level
		return ret_val
			
class roller():	   
	def roll(self,die_range,apply_advantage=0):
		max_vals = self.parse_roll(die_range)
		roll_vals = []		
		cumulative = 0
		for die in max_vals:
			roll_val = {}
			if isinstance(die[0],basestring):
				roll_val['value'] = int(die[0].replace('static_',''))
			else:
				roll_val['rolls'] = [random.randint(1,die[0]),random.randint(1,die[0])]
				advantage_mod = die[1]
				roll_val['die'] = 'd' + str(die[0])
				
				if apply_advantage != 0:
					advantage_mod = apply_advantage
				
				roll_val['advantage'] = advantage_mod
				if advantage_mod == 0:
					roll_val['value'] = roll_val['rolls'][0]
				elif advantage_mod == 1:
					roll_val['value'] = max(roll_val['rolls'])
				else:
					roll_val['value'] = min(roll_val['rolls'])
			
			roll_vals.append(roll_val)
			cumulative += roll_val['value']			
		return {'value': cumulative, 'rolls': roll_vals}
	def parse_roll(self,die_range):
		#parses a die_range
		# can be a list containing numbers or strings
		
		dice = []
		dice_inputs = []
		die_split = []
		nDice = 0
		dVal = 0
		if isinstance(die_range, basestring):
			dice_inputs = [die_range.split('+')]
		else:
			for x in die_range:
				dice_inputs.append(x.split('+'))
		
		for die_split in dice_inputs:
			for x in die_split:
				#looking for form #D#
				i = 0
				adv_mod = 0
				if (x.strip().lower().find("/a") != -1):
					process_text = x.strip().lower().replace('/a','')
					adv_mod = 1
				elif (x.strip().lower().find("/d") != -1):
					process_text = x.strip().lower().replace('/d','')
					adv_mod = -1
				else:
					process_text = x.strip().lower()
					adv_mod = 0
				if process_text[0].isdigit() or process_text[0].lower() == 'd':
					while process_text[0:i + 1].isdigit() and i <= len(process_text):
						i = i + 1
					if (i == 0 or i == len(process_text)):
						nDice = 1	
					else:
						nDice = process_text[0:i]
					
					if process_text.isdigit():
						dVal = 'static_{}'.format(process_text)
						dice.append([dVal,adv_mod])
					else:
						dVal = int(process_text[process_text.find("d")+1:])
						for i in range(0,int(nDice)):
							dice.append([dVal,adv_mod])
		return dice
class name_generator():
	def __init__(self):
		pass
	@staticmethod
	def getName(use_race_names=True,race_description="human",gender='m',tags=[]):
		fname = ''
		lname = ''
		if (use_race_names==True):
			name_db = db()
			tag_str = ' AND (tags like ' 
			for tag in tags:
				tag_str += '\'%' + tag + '%\' OR tags LIKE '
			if tag_str[-len(' OR tags LIKE '):] == ' OR tags LIKE ':
				tag_str = tag_str[0:len(tag_str)- len(' OR tags LIKE ')]
			if tag_str == " AND (tags like ":
				tag_str = ''
			if tag_str != '':
				tag_str += ")"
			#split gender by commas, build forward and reverse list
			g,g_rev = '',''
			for i in range (0,len(gender)):
				if gender[i] == 'm' or gender[i] == 'f':
					g += gender[i] + ','
					g_rev = gender[i] + ',' + g_rev
			g = '%' + g[0:-1] + '%'
			g_rev = '%' + g_rev[0:-1] + '%'
			exec_str = "SELECT * FROM names WHERE type='first' AND race = '" + \
			race_description + "' AND ('" + g + \
			"' like '%' || gender || '%' OR '" + g_rev +\
			"' like '%' || gender || '%' OR gender like '"+g+\
			"' OR gender like '"+g_rev+"')  " + tag_str 
			
			r = name_db.execute(exec_str)
			fn = r.fetchall()
			rand_num = random.randint(0,len(fn)-1)
			fname = fn[rand_num]['name']
			exec_str ="SELECT * FROM names WHERE type='last' AND race = '" + \
			race_description + "' AND ('" + g + \
			"' like '%' || gender || '%' OR '" + g_rev + \
			"' like '%' || gender || '%' OR gender like '"+g+ \
			"' OR gender like '"+g_rev+"')  " + tag_str 
			r = name_db.execute(exec_str)
			fn = r.fetchall()
			rand_num = random.randint(0,len(fn)-1)
			lname = fn[rand_num]['name']
			name_db.connection.close()
		else:
			#random number generator for consonants and vowels
			consonants = ['b','c','ch','ck','d','f','g','h','j','k','l','m','n',
			'p','q','qu','r','s','t','th','v','w','x','y','z']
			vowels = ['a','e','i','o','u','y','igh','ae','ie','au','oo','eu',
			'ue','ai','ia']
			pull_string = [consonants,vowels][random.randint(0,1)]
			for i in range(0, random.randint(1,5) + 2):
				fname = fname + pull_string[random.randint(0,len(pull_string)-1)]
				if pull_string == vowels:
					pull_string = consonants
				else:
					pull_string = vowels
			pull_string = [consonants,vowels][random.randint(0,1)]
			for i in range(0, random.randint(1,5) + 2):
				lname = lname + pull_string[random.randint(0,len(pull_string)-1)]
				if pull_string == vowels:
					pull_string = consonants
				else:
					pull_string = vowels
		return(fname.title() + ' ' + lname.title())
		
class triggerParser(db):
	def __init__(self, parent=None):
		self.parent = parent
		db.__init__(self)
	
	def getAndProcess(self, parent_id=0, parent_table='classes',level_trigger=1):
		self.processTriggers(self.getTriggers(parent_id,parent_table,level_trigger))
		
	
	def getTriggers(self,parent_id=0, parent_table='classes', level_trigger=1):		
		return self.execute("SELECT * FROM triggers WHERE parent_id =:p_id " +\
		"AND parent_table = :p_table AND (trigger_lvl = :lvl)",
		{'p_id':parent_id, 'p_table': parent_table, 'lvl':level_trigger}).fetchall()
	
	def processTriggers(self, trigger_dict):
		'''loop through triggers in dictionary and call appropriate function
		   for the trigger type. Requires Parent to not be null'''
		
		if not isinstance(self.parent,character):
				self.parent = character()
		prev_obj = self.parent
		for i,x in enumerate(trigger_dict):
			print("Processing trigger:\n  Parent: {}-{}\n  Child: {}-{}\n  Level: {}".format(x['parent_table'],x['parent_id'],x['child_table'],x['child_id'],x['trigger_lvl']))
			trigger_type = x['child_table']
			child_ids = str(x['child_id']).split(',')
			for child_id in child_ids:

				if trigger_type == 'classes':
					self.parent.addClass(int(child_id.strip()))
				elif trigger_type == 'races':
					self.parent.addRace(int(child_id.strip()))
				elif trigger_type == 'spells':
					prev_obj = self.parent.addSpell(int(child_id.strip()))
				elif trigger_type == 'enhancements':
					self.parent.addEnhancement(int(child_id.strip()))
				elif trigger_type == 'traits':
					prev_obj = self.parent.addTrait(int(child_id.strip()))
				elif trigger_type == 'proficiencies':
					prev_obj = self.parent.addProficiency(int(child_id.strip()))				
				elif trigger_type == 'checks':
					prev_obj.checks.append[check(int(child_id.strip()))]
				elif trigger_type == 'subclass':
					self.parent.subclass(x['parent_id'])
				elif trigger_type == 'subrace':
					self.parent.subrace(x['parent_id'])		   


# GUI Portion -----------------------------------------------------------------

from tkinter import *
from tkinter import ttk
from tkinterhtml import *


''' Screen Layout
Top Bar:
	- Player Name
	- Player Level
	- Player HP
Left Bar:
	- Attributes
	- Skills
	- Player Race(s)
	- Player Class(es)
Main Pane:
	- Tab View
		- Traits
		- Spells
		- Inventory
'''

class ToggledFrame(tk.Frame):

	def __init__(self, parent, text="", *args, **options):
		tk.Frame.__init__(self, parent, *args, **options)

		self.show = tk.IntVar()
		self.show.set(0)

		self.title_frame = ttk.Frame(self)
		self.title_frame.pack(fill="x", expand=1)

		ttk.Label(self.title_frame, text=text).pack(side="left", fill="x", expand=1)

		self.toggle_button = ttk.Checkbutton(self.title_frame, width=2, text='+', command=self.toggle,
											variable=self.show, style='Toolbutton')
		self.toggle_button.pack(side="left")

		self.sub_frame = tk.Frame(self, relief="sunken", borderwidth=1)

	def toggle(self):
		if bool(self.show.get()):
			self.sub_frame.pack(fill="x", expand=1)
			self.toggle_button.configure(text='-')
		else:
			self.sub_frame.forget()
			self.toggle_button.configure(text='+')


class skill_widgets():
	def __init__(self, parent_frame, skill_obj=None, grid_row=0):
		self.parent_frame = parent_frame
		self.lbl = Label(self.parent_frame)
		self.value_entry = Entry(self.parent_frame, text=0, width=4)
		self.lbl.grid(row=grid_row,column=0)
		self.value_entry.grid(row=grid_row,column=1)
	def linkSkill(self,skill_obj):
		self.skill = skill_obj

class dnd_app():
	def __init__(self):
		self.root = Tk()
		self.createWidgets()
		self.character = None		
		#self.loadCharacter()
		self.startWindow()

	def loadCharacter(self, char_object = None):
		if char_object == None:
			self.character = character()
		else:
			self.character = char_object
	   
		self.name_box.delete(0,END)
		self.name_box.insert(0, self.character.name)
		
		self.level_box.delete(0,END)
		self.level_box.insert(0, self.character.level())
		for attrib in self.attributes:
			attrib['label'].pack_forget()
			attrib['value'].pack_forget()
		for skill_id in self.skills:
			skill_id['label'].pack_forget()
			skill_id['value'].pack_forget()
		self.attributes.clear()
		self.skills.clear()
		i = 0
		for attrib in self.character.attributes.keys():
			c_attrib =self.character.attributes[attrib]
			clbl = Label(self.attribute_frame, text=attrib.title())
			cvalue = Entry(self.attribute_frame, text=c_attrib.score,width=4)
			cmod = Entry(self.attribute_frame, text=self.character.getAttrMod(attrib),width=4)
			self.attributes[attrib] = {
			'label': clbl, 
			'value': cvalue,
			'mod': cmod}
			self.attributes[attrib]['label'].grid(row=i,column=0)
			self.attributes[attrib]['value'].grid(row=i,column=1)
			self.attributes[attrib]['mod'].grid(row=i,column=2)
			i+=1
		i = 0
		for skill_id in self.character.skills.keys():
			c_skill =self.character.skills[skill_id]			
			self.skills[skill_id] = {
			'label': Label(self.skill_frame, text=skill_id.title()), 
			'value': Entry(self.skill_frame, text=c_skill.getScore(),width=4)}
			self.skills[skill_id]['label'].grid(row=i,column=0)
			self.skills[skill_id]['value'].grid(row=i,column=1)
			i+=1
	def createWidgets(self):
		#allow second row to grow
		self.root.grid_rowconfigure(0, weight=0)
		self.root.grid_rowconfigure(1, weight=1)
		self.root.grid_columnconfigure(0, weight=1)
		self.root.grid_columnconfigure(1, weight=1)
		#setup left bar and widgets
		self.left_bar = Frame(self.root)
		self.left_bar.grid(row=1, column=0, columnspan=1)
		self.attribute_label = Label(self.left_bar, text='Attributes')
		self.attribute_label.grid(row=0, column=0)
		self.attribute_frame = Frame(self.left_bar)
		self.attribute_frame.grid(row=1,column=0)
		i = 0
		self.strength_lbl = Label(self.attribute_frame,text="Strength")
		self.strength_value = Entry(self.attribute_frame, text=0, width=4)
		self.strength_mod = Entry(self.attribute_frame, text=0, width=4)
		self.strength_lbl.grid(row=i,column=0)
		self.strength_value.grid(row=i,column=1)
		self.strength_mod.grid(row=i,column=2)
		i+=1
		self.dexterity_lbl = Label(self.attribute_frame,text="Dexterity")
		self.dexterity_value = Entry(self.attribute_frame, text=0, width=4)
		self.dexterity_mod = Entry(self.attribute_frame, text=0, width=4)
		self.dexterity_lbl.grid(row=i,column=0)
		self.dexterity_value.grid(row=i,column=1)
		self.dexterity_mod.grid(row=i,column=2)
		i+=1
		self.constitution_lbl = Label(self.attribute_frame,text="Constitution")
		self.constitution_value = Entry(self.attribute_frame, text=0, width=4)
		self.constitution_mod = Entry(self.attribute_frame, text=0, width=4)
		self.constitution_lbl.grid(row=i,column=0)
		self.constitution_value.grid(row=i,column=1)
		self.constitution_mod.grid(row=i,column=2)
		i+=1
		self.intelligence_lbl = Label(self.attribute_frame,text="Intelligence")
		self.intelligence_value = Entry(self.attribute_frame, text=0, width=4)
		self.intelligence_mod = Entry(self.attribute_frame, text=0, width=4)
		self.intelligence_lbl.grid(row=i,column=0)
		self.intelligence_value.grid(row=i,column=1)
		self.intelligence_mod.grid(row=i,column=2)
		i+=1
		self.wisdom_lbl = Label(self.attribute_frame,text="Wisdom")
		self.wisdom_value = Entry(self.attribute_frame, text=0, width=4)
		self.wisdom_mod = Entry(self.attribute_frame, text=0, width=4)
		self.wisdom_lbl.grid(row=i,column=0)
		self.wisdom_value.grid(row=i,column=1)
		self.wisdom_mod.grid(row=i,column=2)
		i+=1
		self.charisma_lbl = Label(self.attribute_frame,text="Charisma")
		self.charisma_value = Entry(self.attribute_frame, text=0, width=4)
		self.charisma_mod = Entry(self.attribute_frame, text=0, width=4)
		self.charisma_lbl.grid(row=i,column=0)
		self.charisma_value.grid(row=i,column=1)
		self.charisma_mod.grid(row=i,column=2)
		i=0
		'''
		self.acrobatics_lbl = Label(self.skill_frame,text="Acrobatics")
		self.acrobatics_value = Entry(self.skill_frame, text=0, width=4)
		self.acrobatics_lbl.grid(row=i,column=0)
		self.acrobatics_value.grid(row=i,column=1)
		i+=1
		self.animal_handling_lbl = Label(self.skill_frame,text="Animal Handling")
		self.animal_handling_value = Entry(self.skill_frame, text=0, width=4)
		self.animal_handling_lbl.grid(row=i,column=0)
		self.animal_handling_value.grid(row=i,column=1)
		i+=1
		self.arcana_lbl = Label(self.skill_frame,text="Arcana")
		self.arcana_value = Entry(self.skill_frame, text=0, width=4)
		self.arcana_lbl.grid(row=i,column=0)
		self.arcana_value.grid(row=i,column=1)
		i+=1
		self.athletics_lbl = Label(self.skill_frame,text="Athletics")
		self.athletics_value = Entry(self.skill_frame, text=0, width=4)
		self.athletics_lbl.grid(row=i,column=0)
		self.athletics_value.grid(row=i,column=1)
		i+=1
		self.deception_lbl = Label(self.skill_frame,text="Deception")
		self.deception_value = Entry(self.skill_frame, text=0, width=4)
		self.deception_lbl.grid(row=i,column=0)
		self.deception_value.grid(row=i,column=1)
		i+=1
		self.history_lbl = Label(self.skill_frame,text="History")
		self.history_value = Entry(self.skill_frame, text=0, width=4)
		self.history_lbl.grid(row=i,column=0)
		self.history_value.grid(row=i,column=1)
		i+=1
		self.insight_lbl = Label(self.skill_frame,text="Insight")
		self.insight_value = Entry(self.skill_frame, text=0, width=4)
		self.insight_lbl.grid(row=i,column=0)
		self.insight_value.grid(row=i,column=1)
		i+=1
		self.intimidation_lbl = Label(self.skill_frame,text="Intimidation")
		self.intimidation_value = Entry(self.skill_frame, text=0, width=4)
		self.intimidation_lbl.grid(row=i,column=0)
		self.intimidation_value.grid(row=i,column=1)
		i+=1
		self.investigation_lbl = Label(self.skill_frame,text="Investigation")
		self.investigation_value = Entry(self.skill_frame, text=0, width=4)
		self.investigation_lbl.grid(row=i,column=0)
		self.investigation_value.grid(row=i,column=1)
		i+=1
		self.medicine_lbl = Label(self.skill_frame,text="Medicine")
		self.medicine_value = Entry(self.skill_frame, text=0, width=4)
		self.medicine_lbl.grid(row=i,column=0)
		self.medicine_value.grid(row=i,column=1)
		i+=1
		self.nature_lbl = Label(self.skill_frame,text="Nature")
		self.nature_value = Entry(self.skill_frame, text=0, width=4)
		self.nature_lbl.grid(row=i,column=0)
		self.nature_value.grid(row=i,column=1)
		i+=1
		self.nature_lbl = Label(self.skill_frame,text="Nature")
		self.nature_value = Entry(self.skill_frame, text=0, width=4)
		self.nature_lbl.grid(row=i,column=0)
		self.nature_value.grid(row=i,column=1)
		i+=1
		self.perception_lbl = Label(self.skill_frame,text="Perception")
		self.perception_value = Entry(self.skill_frame, text=0, width=4)
		self.perception_lbl.grid(row=i,column=0)
		self.perception_value.grid(row=i,column=1)
		i+=1
		self.performance_lbl = Label(self.skill_frame,text="Performance")
		self.performance_value = Entry(self.skill_frame, text=0, width=4)
		self.performance_lbl.grid(row=i,column=0)
		self.performance_value.grid(row=i,column=1)
		i+=1
		self.performance_lbl = Label(self.skill_frame,text="Performance")
		self.performance_value = Entry(self.skill_frame, text=0, width=4)
		self.performance_lbl.grid(row=i,column=0)
		self.performance_value.grid(row=i,column=1)
		i+=1
		'''
		self.skill_label = Label(self.left_bar, text='Skills')
		self.skill_label.grid(row=2,column=0)
		self.skill_frame = Frame(self.left_bar)
		self.skill_frame.grid(row=3,column=0)
		self.skills = {}
		for skill_id in []:
			self.skills[skill_id] = skill_widgets(parent_frame=self.skill_frame,
			grid_row=i)
			i+=1
		self.skill_frame.pack_slaves()
		#setup top bar and widgets
		self.top_bar = Frame(self.root)
		self.top_bar.grid(row=0, column=0, columnspan=2)
		self.name_label = Label(self.top_bar,text="Name: ")
		self.name_box = Entry(self.top_bar)
		self.name_label.grid(row=0,column=0)
		self.name_box.grid(row=0,column=1)
		self.level_label = Label(self.top_bar,text="Level: ")
		self.level_box = Entry(self.top_bar)
		self.level_label.grid(row=0,column=2)
		self.level_box.grid(row=0,column=3)
		#setup main window
		self.main_window = Frame(self.root)
		self.main_window.grid(row=1,column=1,columnspan=1)
	def startWindow(self):
		self.root.mainloop()
