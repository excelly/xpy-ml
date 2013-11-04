import sys
from math import ceil, floor
from PIL import Image

def usage():
	print '''python split_image.py input_image_file num_rows num_cols
	'''
	sys.exit(1)

if __name__ == '__main__':
	if len(sys.argv) != 4:
		usage()
		
	input_file = sys.argv[1]
	nrow = int(sys.argv[2])
	ncol = int(sys.argv[3])
	
	im = Image.open(input_file)
	w, h = im.size
	sub_w = int(floor(w/ncol))
	sub_h = int(floor(h/nrow))
	for i in range(nrow):
		rows = (i*sub_h, (i+1)*sub_h)
		for j in range(ncol):	
			cols = (j*sub_w, (j+1)*sub_w)
			block = (cols[0], rows[0], cols[1], rows[1])
			print 'Processing block: ', block
			
			sub = im.crop(block)
			out_file = '%s-%d-%d.png' % (input_file, i+1, j+1)
			sub.save(out_file)
