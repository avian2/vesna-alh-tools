import alh
import common
from optparse import OptionParser
import sys

class NodeInfo: 
	def __init__(self):
		self.hello = None
		self.firstcall = None

def query_node(node):
	nodeinfo = NodeInfo()

	try:
		nodeinfo.hello = node.get("hello").strip()
		nodeinfo.firstcall = node.get("prog/firstcall").strip()
	except:
		nodeinfo.ok = False
	else:
		nodeinfo.ok = True

	return nodeinfo

def get_neigbors(node):
	try:
		#node.post("prog/firstcall", "1")
		r = node.get("radio/neighbors")
	except Exception, e:
		print "Failed:", e
		return

	for line in r.split("\r\n"):
		fields = line.split(" | ")
		if len(fields) == 6:
			try:
				yield int(fields[3])
			except ValueError:
				pass

def print_stats(visited):
	visited = sorted((id, info) for id, info in visited.iteritems())

	print "ID\tOnline\tVersion\tFirst call"
	for id, info in visited:

		if info.hello:
			info.hello = info.hello.replace(
					"Hello Application version ", "")

		if info.firstcall:
			info.firstcall = info.firstcall.replace(
					"firstCallFlag is ", "")

		row = [	
			id,
			info.ok,
			info.hello,
			info.firstcall
		]

		print '\t'.join(map(str, row))


def main():
	parser = OptionParser(usage="%prog [options]")

	common.add_communication_options(parser)

	parser.add_option("-o", "--output", dest="output", metavar="PATH",
			help="PATH to write dotfile to")

	(options, args) = parser.parse_args()

	coordinator = common.get_coordinator(options)	

	queue = [0]
	visited = {}

	if options.output:
		outf = open(options.output, "w")
	else:
		outf = sys.stdout

	outf.write("digraph net {\n")

	n = 0
	while queue:
		current_id = queue.pop()
		if current_id not in visited:
			print "*** Query node ID:", current_id

			if current_id == 0:
				node = coordinator
			else:
				node = alh.ALHProxy(coordinator, current_id)

			visited[current_id] = query_node(node)

			for next_id in get_neigbors(node):
				outf.write("n%d -> n%d\n" % (current_id, next_id))
				queue.insert(0, next_id)

	outf.write("}\n")

	print_stats(visited)

main()
