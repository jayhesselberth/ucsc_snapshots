# ucsc\_snapshots documentation

**Version**: 0.1.6

## Summary

ucsc\_snapshots retrieves pictures from UCSC Genome Browser based on
coordinates specified from BED3+ file and a session ID (hgsid).

UCSC Genome Browser should be set up with tracks prior to using the
utility and saved as a session. This includes all track settings, sizes
etc.  Once these are setup, you can load the page source and identify the
hgsid by searching for "hgsid="

Supply the hgsid and a BED file. Images will be retrieved based on the
coordinates in the BED file and saved to the directory as:

    ucsc-snapshots-<hgsid>/chrom-start-end.pdf

    ucsc-snapshots-<hgsid>/chrom-start-end.png

## Warnings

if you have many regions, you may need to run this overnight as thet
UCSC limit s 1 request per 15 sec and 5000 requests per day.

**Beware** of multiple procs accessessing the same hgsid at the same time,
they will affect each other's strand settings

## Examples

The simplest case, just fetch images:

    ucsc_snapshots BED3+ SESSIONID

Retrieve snapshots maintaining the display with 5'->3' orientation using
the strand field from the BED file:

    ucsc_snapshots BED3+ SESSIONID --reverse-display

Add an annotation to the output directory
(directory becomes ucsc-snapshots-<hgsid>-annotation/):

    ucsc_snapshots BED3+ SESSIONID --dir-annotation celltype=MCF7

Output PNG files only (default is PDF and PNG):

    ucsc_snapshots BED3+ SESSIONID --img-types png

## Installation

    pip install ucsc_snapshots

