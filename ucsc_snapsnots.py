#! /usr/bin/env python

''' ucsc_snapshots: retrieve pictures from the UCSC Genome Browser based on
coordinates specified from BED3+ file and a session ID (hgsid).

UCSC Genome Browser should be set up with tracks prior to using the
utility and saved as a session. This includes all track settings, sizes etc.
Once these are setup, load the page source and identify the hgsid by
searching for "hgsid="

Supply the hgsid and a BED file. Images will be retrieved based on the
coordinates in the BED file and saved to the directory as::

    ucsc-snapshots-<hgsid>/chrom-start-end.pdf
    ucsc-snapshots-<hgsid>/chrom-start-end.png

..note::

    beware of multiple procs accessessing the same hgsid at
    the same time, they will affect each other's strand settings

..warning::

    if you have many regions, you will need to run this overnight
    (e.g. via a job submitted to the LSF night queue), otherwise UCSC will
    throttle your connection (limit 1 request / 15 sec, 5000 requests per day)

'''

import sys
import re
import time

import ucscsession
from pybedtools import BedTool
from path import path

__author__ = 'Jay Hesselberth'
__contact__ = 'jay.hesselberth@gmail.com'
__version__ = '$Revision: 546 $'

def ucsc_snapshots(bedfilename, session_id, rev_display, dir_annots,
                   img_types, no_delay, verbose):

    ucscsession.settings.hgsid = session_id
    session = Session(rev_display, no_delay, verbose)

    # for each BED field, set params on the UCSC browser and fetch the
    # images
    for region in BedTool(bedfilename):
    
        position = '%s:%s-%s' % (region.chrom, region.start, region.end)

        session.set_position(position)

        for imgtype in img_types:

            filename = getfilename(session_id, position,
                                   name=region.name, score=region.score,
                                   annots=dir_annots, ext=imgtype)
            session.write_image(imgtype=imgtype, filename=filename,
                                strand=region.strand)

class Session(ucscsession.session._UCSCSession):

    def __init__(self, rev_display, no_delay, verbose):

        ucscsession.session._UCSCSession.__init__(self)

        self.verbose = verbose

        # keep track of the flipped state in the session. if flipped is
        # True, will show neg strand genes 5'->3'
        self.rev_display = rev_display
        flipped = self._find_flipped_state()

        self.flipped = flipped

        # XXX no_delay for debugging only
        if no_delay:
            self._SLEEP = 1
        else:
            # required minimum time between requests per UCSC
            self._SLEEP = 15

    def write_image(self, imgtype, filename, strand):
        ''' wrapper for image generation. writes requested content to
        filename.
        
        only PDF and PNG are currently supported.'''
        # XXX could add more image capability by converting retrieved png
        # files to jpeg, tif etc.
        if imgtype.lower() == 'pdf':
            content = self.pdf(strand)
        elif imgtype.lower() == 'png':
            content = self.png(strand)
        else:
            raise OSError, ">> image type %s not supported" % imgtype

        with open(filename, 'w') as fileout:
            fileout.write(content)

        if self.verbose:
            print >>sys.stderr, ">> wrote %s" % filename

    def pdf(self, strand):
        """ 
        retrieve PDF of the current browser view for currently set
        position.

        returns: pdf content
        """
        payload = {'hgt.psOutput':'on'}

        # deal with display flipping
        payload = self._flip_display(strand, payload)

        response = self.session.post(self.tracks_url, data=payload)

        time.sleep(self._SLEEP)

        link = ucscsession.helpers.pdf_link(response)

        content = self.session.get(link).content

        return content

    def png(self, strand):
        """ 
        retrieve merged PNG of the current browser view for currently set
        position.

        returns: png content
        """
        # these CGI settings ensure the browser returns a single, merged
        # PNG for the viewport
        payload = {'hgt.imageV1':1,
                   'hgt.trackImgOnly':1}

        # deal with display flipping
        payload = self._flip_display(strand, payload)

        # example: <IMG SRC='../trash/hgt/hgt_genome_6243_68cdb0.png'
        img_regex = re.compile('<IMG SRC=\'\.\.\/(trash\/hgt\/hgt_.*\.png)')

        response = self.session.post(self.tracks_url, data=payload)
        imgfilename = img_regex.findall(response.text)[0]

        time.sleep(self._SLEEP)

        link = 'http://genome.ucsc.edu/' + imgfilename
        content = self.session.get(link).content

        return content

    def _flip_display(self, strand, payload):
        ''' flip display for such that all genes (pos and neg strands) are
        shown 5'->3'
        
        adds hgt.toggleRevCmplDisp to CGI payload if required

        ..note: beware of multiple procs accessessing the same hgsid at
        the same time, they will affect each other's strand settings '''

        # the CGI var is a true toggle so must be flipped back to e.g.
        # pos strand genes after a neg strand gene is retrieved and vice
        # versa

        if strand == '-' and self.rev_display and not self.flipped:
            payload['hgt.toggleRevCmplDisp'] = '1'
            self.flipped = True

        elif strand == '+' and self.rev_display and self.flipped:
            payload['hgt.toggleRevCmplDisp'] = '1'
            self.flipped = False

        return payload

    def _find_flipped_state(self):
        ''' determine whether the display is currently flipped.
        
        returns: bool'''
        cart_info = self.cart_info()
        db = cart_info['db']
        comp_key = 'hgt.revCmplDisp_%s' % db

        try:
            state = cart_info[comp_key]
        except KeyError:
            msg = ">> flipped state not avail in %s" % comp_key
            raise KeyError, msg

        # possible vals are 0 and 1
        if int(state) == 0:
            return False
        else:
            return True

def getfilename(session_id, position, name, score, annots, ext='pdf'):
    ''' generate a filename for the image output.
    
    creates directory if it does not exist.
    
    position is required.
    if name and score are specified, filename is:
    <name>-<score>-<pos>.pdf
    '''
    imgdir = 'ucsc-snapshots-hgsid-%s' % session_id
    
    if annots:
        for key, val in annots:
            imgdir += '-%s-%s' % (key, val)

    imgdir = path(imgdir)

    if not imgdir.exists():
        imgdir.mkdir()

    # chr:1-2 -> chr-1-2
    pos = position.replace(':','-')

    fname = pos
    if score != '.':
        fname = '%s-%s' % (score, fname)
    if name != '.':
        fname = '%s-%s' % (name, fname)

    imgfilename = path('%s.%s' % (fname, ext.lower()))
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

    parser.add_option("--img-types", action="append",
        default=[], help="image types to write. "
                            "(default: PNG, PDF)")

    parser.add_option("--dir-annotations", action="append",
        default=[], help="additional key=value pairs for annotating "
                          "output directory. (default: None)")

    parser.add_option("--no-delay", action="store_true",
        default=False, help="no delay between requests. for debugging "
                            "only. "
                            "(default: %default)")

    parser.add_option("--reverse-display", action="store_true",
        default=False, help="reverse display for neg strand genes "
                            "(default: %default)")

    parser.add_option("-v", "--verbose", action="store_true",
        default=False, help="verbose output (default: %default)")

    options, args = parser.parse_args(args)

    if len(args) < 2:
        parser.error("specify BED filename and UCSC session ID")

    if len(options.img_types) == 0:
        options.img_types.extend(['PDF','PNG'])

    return options, args

def main(args=sys.argv[1:]):
    options, args = parse_options(args)
    bedfilename = args[0]
    sessionid = args[1]

    if options.dir_annotations:
        annots = [(i.split('=')) for i in options.dir_annotations]

    kwargs = {'verbose':options.verbose,
              'img_types':options.img_types,
              'rev_display':options.reverse_display,
              'dir_annots':annots,
              'no_delay':options.no_delay}
    return ucsc_snapshots(bedfilename, sessionid, **kwargs)

if __name__ == '__main__':
    sys.exit(main())

