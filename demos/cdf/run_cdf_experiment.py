import datetime
import logging
import sys
from vesna import cdf
from vesna.cdf.xml import CDFXMLExperiment

logging.basicConfig(level=logging.INFO)

def main():
	if len(sys.argv) != 3:
		print "USAGE: %s input-cdf output-cdf" % (sys.argv[0],)
		return
	else:
		inp_path = sys.argv[1]
		out_path = sys.argv[2]

		f = open(inp_path)
		ex = CDFXMLExperiment.load(f)
		
		e = ex.get_experiment()

		i = cdf.CDFExperimentIteration()
		e.run(i)

		out_base = out_path.replace(".cdf", "")
		ex.save_all(out_base)

main()
