#Copyright (C) 2020 Inter-University Institute for Data Intensive Astronomy
#See processMeerKAT.py for license details.

import os
import sys
import glob
from shutil import copytree

import config_parser
from config_parser import validate_args as va
from cal_scripts import bookkeeping

import logging
logger = logging.getLogger(__name__)
logging.basicConfig(format="%(asctime)-15s %(levelname)s: %(message)s", level=logging.INFO)

def sortbySPW(visname):
    return float(visname.split('~')[0])

def check_output(fname,pattern,out,job='concat',filetype='image'):

    files = glob.glob(pattern)
    if os.path.exists(out):
        logger.info('Output file "{0}" already exists. Skipping {1}.'.format(out,job))
        return None
    elif len(files) == 0:
        logger.warn("Didn't find any {0}s with '{1}'".format(filetype,pattern))
        return None
    elif len(files) == 1:
        logger.warn("Only found 1 {0} with '{1}'. Will copy to this directory.".format(filetype,pattern))
        copytree(files[0], out)
        return None
    return files

def do_concat(visname, fields):

    logger.info('Beginning {0}.'.format(sys.argv[0]))
    basename, ext = os.path.splitext(visname)
    filebase = os.path.split(basename)[1]
    msmd.open(visname)
    for target in fields.targetfield.split(','):
        fname = msmd.namesforfields(int(target))[0]

        #Concat images (into continuum cube)
        pattern = '*MHz/images/*{0}*image'.format(fname)
        out = '{0}.{1}.contcube'.format(filebase,fname)
        images = check_output(fname,pattern,out,job='imageconcat',filetype='image')
        if images is not None:
            images.sort(key=sortbySPW)
            logger.info('Creating continuum cube with following command:')
            logger.info('ia.imageconcat(infiles={0}, outfile={1}, axis=-1, relax=True)'.format(images,out))
            ia.imageconcat(infiles=images, outfile=out, axis=-1, relax=True)

        if os.path.exists(out):
            if not os.path.exists(out+'.fits'):
                exportfits(imagename=out, fitsimage=out+'.fits')
        else:
            logger.error("Output image '{0}' not written.".format(out))

        #Concat MSs
        pattern = '*MHz/*{0}*.ms'.format(fname)
        out = '{0}.{1}.ms'.format(filebase,fname)
        MSs = check_output(fname,pattern,out,job='concat',filetype='MS')
        if MSs is not None:
            MSs.sort(key=sortbySPW)
            logger.info('Concatenating MSs with following command:')
            logger.info('concat(vis={0}, concatvis={1})'.format(MSs,out))
            concat(vis=MSs, concatvis=out)

        if not os.path.exists(out):
            logger.error("Output MS '{0}' not written.".format(out))

        #Concat MMSs
        pattern = '*MHz/*{0}*.mms'.format(fname)
        out = '{0}.{1}.mms'.format(filebase,fname)
        MMSs = check_output(fname,pattern,out,job='virtualconcat',filetype='MMS')
        if MMSs is not None:
            MMSs.sort(key=sortbySPW)
            logger.info('Concatenating MMSs with following command:')
            logger.info('virtualconcat(vis={0}, concatvis={1})'.format(MMSs,out))
            virtualconcat(vis=MMSs, concatvis=out)

        if not os.path.exists(out):
            logger.error("Output MMS '{0}' not written.".format(out))

    msmd.done()
    logger.info('Completed {0}.'.format(sys.argv[0]))

if __name__ == '__main__':
    # Get the name of the config file
    args = config_parser.parse_args()

    # Parse config file
    taskvals, config = config_parser.parse_config(args['config'])

    visname = va(taskvals, 'data', 'vis', str)
    spw = va(taskvals, 'crosscal', 'spw', str, default='')
    fields = bookkeeping.get_field_ids(taskvals['fields'])

    do_concat(visname, fields)
