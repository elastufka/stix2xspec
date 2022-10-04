from stix2xspec.stix2xspec import convert_spectrogram
from importlib import resources

if __name__ == "__main__" :

    fitsfile = resources.path('stix2xspec.data', 'solo_L1A_stix-sci-spectrogram-2207238956_20220723T122007-20220723T182511_079258_V01.fits')
    bgfile = resources.path('stix2xspec.data', 'solo_L1A_stix-sci-xray-l1-2207235029_20220723T113947-20220723T122747_079205_V01.fits')
    with fitsfile as aa, bgfile as bb:
        outfile = convert_spectrogram(str(aa), str(bb), to_fits = True, testing = False)

