#! /usr/bin/env python

''' ucsc_snapshots: retrieve pictures from UCSC Genome Browser based on
coordinates specified from BED3+ file.

UCSC Genome Browser should be set up with tracks prior to using the
utility. This includes all track settings, sizes etc. Once these are
setup, you can load the page source and identify the hgsid by
searching for "hgsid="

Supply the hgsid and a BED file. Images will be retrieved based on the
coordinates in the BED file and saved to the directory as:

ucsc-snapshots-<hgsid>/chrom-start-end.pdf and
ucsc-snapshots-<hgsid>/chrom-start-end.png

WARNING: if you have many regions, you will need to run this overnight
(e.g. via a job submitted to the LSF night queue), otherwise UCSC will
throttle your connection (limit 1 request / 15 sec, 5000 requests per day)
'''

# TODO:
# ...

import sys
import re
import time

import ucscsession
from pybedtools import BedTool
from path import path

__author__ = 'Jay Hesselberth'
__contact__ = 'jay.hesselberth@gmail.com'
__version__ = '$Revision: 538 $'

def ucsc_snapshots(bedfilename, session_id, verbose):

    ucscsession.settings.hgsid = session_id
    session = Session()

    # for each BED field, set params on the UCSC browser and fetch the
    # images
    for region in BedTool(open(bedfilename)):
    
        position = '%s:%s-%s' % (region.chrom, region.start,
                                 region.end)

        session.set_position(position)

        pdffile = getfilename(session_id, position,
                              name=region.name, score=region.score)

        session.pdf(filename=pdffile)

        if verbose:
            print >>sys.stderr, ">> writing %s" % pdffile 

        pngfile = getfilename(session_id, position, 
                              name=region.name, score=region.score,
                              ext='png')
        session.png(filename=pngfile)

        if verbose:
            print >>sys.stderr, ">> writing %s" % pngfile 

class Session(ucscsession.session._UCSCSession):
    def png(self, position=None, filename=None):
        """ 
        Save a PNG of the current browser view.

        If `position` is None, then use the last available position.

        Returns the created filename.
        """
        # these CGI settings ensure the browser returns a single, merged
        # PNG for the viewport
        payload = {'hgt.imageV1':1,
                   'hgt.trackImgOnly':1}

        payload.update(position=self._position_string(position))

        # example: 
        # <IMG SRC='../trash/hgt/hgt_genome_6243_68cdb0.png'
        img_regex = re.compile('<IMG SRC=\'\.\.\/(trash\/hgt\/hgt_.*\.png)')

        response = self.session.post(self.tracks_url, data=payload)
        imgfilename = img_regex.findall(response.text)[0]

        time.sleep(self._SLEEP)

        base_url = 'http://genome.ucsc.edu/'
        png_content = self.session.get(base_url + imgfilename)

        fout = open(filename, 'w')
        fout.write(png_content.content)
        fout.close()

        return filename

def getfilename(session_id, position, name, score, ext='pdf'):
    ''' generate a filename for the PDF output. create directory if
    needed.
    
    position: required
    if name and score are specified, filename is:
    <name>-<score>-<pos>.pdf
    '''
    imgdir = path('ucsc-snapshots-hgsid-%s' % session_id)

    if not imgdir.exists():
        imgdir.mkdir()

    # chr:1-2 -> chr-1-2
    pos = position.replace(':','-')

    fname = pos
    if score != '.':
        fname = '%s-%s' % (score, fname)
    if name != '.':
        fname = '%s-%s' % (name, fname)

    imgfilename = path('%s.%s' % (fname, ext))
    imgfilepath = imgdir.joinpath(imgfilename)

    return imgfilepath

def parse_options(args):
    from optparse import OptionParser

    usage = "%prog [OPTION]... BED3+ UCSC-hgsid"
    version = "%%prog %s" % __version__
    description = ("retrieve images from UCSC based on BED regions and "
                   "UCSC session ID ('hgsid')")

    parser = OptionParser(usage=usage, version=version,
                          description=description)

    parser.add_option("-v", "--verbose", action="store_true",
        default=False, help="verbose output (default: %default)")

    options, args = parser.parse_args(args)

    if len(args) < 2:
        parser.error("specify BED filename and UCSC session ID")
  
    return options, args

def main(args=sys.argv[1:]):
    options, args = parse_options(args)
    bedfilename = args[0]
    sessionid = args[1]
    kwargs = {'verbose':options.verbose}
    return ucsc_snapshots(bedfilename, sessionid, **kwargs)

if __name__ == '__main__':
    sys.exit(main())

