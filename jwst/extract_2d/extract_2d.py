#
#  Top level module for 2d extraction.
#

import logging

from .nirspec import nrs_extract2d
from .grisms import extract_grism_objects, extract_tso_object

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def extract2d(input_model,
              slit_name=None,
              apply_wavecorr=False,
              reference_files={},
              grism_objects=None,
              extract_height=None,
              extract_orders=None,
              mmag_extract=99.):
    """
    The main extract_2d function

    Parameters
    ----------
    input_model : `~jwst.datamodels.ImageModel` or `~jwst.datamodels.CubeModel`
    slit_name : str or int
        Slit name.
    apply_wavecorr : bool
        Flag whether to apply the zero point wavelength correction to
        Nirspec exposures.
    reference_files : dict
        Reference files.
    grism_objects : list
        A list of grism objects.
    extract_height: int
        Cross-dispersion extraction height to use for time series grisms.
        This will override the default which for NRC_TSGRISM is a set
        size of 64 pixels.

    Returns
    -------
    output_model : `~jwst.datamodels.ImageModel` or `~jwst.datamodelsCubeModel`
      A copy of the input_model that has been processed.

    """
    nrs_modes = ['NRS_FIXEDSLIT', 'NRS_MSASPEC', 'NRS_BRIGHTOBJ',
                 'NRS_LAMP', 'NRS_AUTOFLAT']
    slitless_modes = ['NIS_WFSS', 'NRC_WFSS', 'NRC_TSGRISM']

    exp_type = input_model.meta.exposure.type.upper()
    log.info('EXP_TYPE is {0}'.format(exp_type))

    if exp_type in nrs_modes:
        if input_model.meta.instrument.grating.lower() == "mirror":
            # Catch the case of EXP_TYPE=NRS_LAMP and grating=MIRROR
            log.info("'EXP_TYPE {} with grating=MIRROR not supported for extract 2D".format(exp_type))
            input_model.meta.cal_step.extract_2d = 'SKIPPED'
            return input_model
        output_model = nrs_extract2d(input_model,
                                     slit_name=slit_name,
                                     apply_wavecorr=apply_wavecorr,
                                     reference_files=reference_files)
    elif exp_type in slitless_modes:
        if exp_type == 'NRC_TSGRISM':
            if extract_height is None:
                extract_height = 64
            output_model = extract_tso_object(input_model,
                                              reference_files=reference_files,
                                              extract_height=extract_height,
                                              extract_orders=extract_orders)
        else:
            # TODO: temp to check fits_wcs catalog use, remove with #2533
            if exp_type == 'NRC_WFSS':
                use_fits_wcs = True
            else:
                use_fits_wcs = False

            output_model = extract_grism_objects(input_model,
                                                 grism_objects=grism_objects,
                                                 reference_files=reference_files,
                                                 extract_orders=extract_orders,
                                                 use_fits_wcs=use_fits_wcs,
                                                 mmag_extract=99.)

    else:
        log.info("'EXP_TYPE {} not supported for extract 2D".format(exp_type))
        input_model.meta.cal_step.extract_2d = 'SKIPPED'
        return input_model

    # Set the step status to COMPLETE
    output_model.meta.cal_step.extract_2d = 'COMPLETE'
    del input_model
    return output_model
