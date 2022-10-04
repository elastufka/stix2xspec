# test second example in README
from stix2xspec.stix2xspec import Spectrogram
from importlib import resources

if __name__ == "__main__" :

    fitsfile = resources.path('stix2xspec.data', 'solo_L1A_stix-sci-spectrogram-2207238956_20220723T122007-20220723T182511_079258_V01.fits')
    bgfile = resources.path('stix2xspec.data', 'solo_L1A_stix-sci-xray-l1-2207235029_20220723T113947-20220723T122747_079205_V01.fits')
    with fitsfile as aa, bgfile as bb:
        spec = Spectrogram(str(aa))
        spec.apply_elut()
        spec.correct_counts()
        spec._counts_to_rate()
        spec.spectrum_to_fits("test_example2.fits")
        
        spec_bg = Spectrogram(str(bb), background = True, use_discriminators = False)
        spec_bg.apply_elut()
        spec_bg.correct_counts()
        #spec_bg.spectrum_to_fits("test_example2_bg.fits") not yet implemented

