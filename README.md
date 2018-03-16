# RE-OCR #

## GoogleCloud Vision API ##

### Install python library for the google cloud vision api ###

  `$ git clone https://github.com/GoogleCloudPlatform/cloud-vision.git`

  `$ cd cloud-vision/python/label|text`

  `$ sudo pip install -r requirements.txt`

   or `$ sudo pip install --upgrade google-cloud-vision`

### In case of Anaconda ###
   `$ conda install -c conda-forge google-api-python-client`


## PDF to JPGs ##

### PDF utils on Ubuntu ###
    convert pdf to jpg with pdftoppm
    install the pdftoppm
     `$  sudo apt-get install poppler-utils`

    convert the pdf file to the image file with command line
    `$ pdf2jpg_ppm(in_name='../data/Endesa1.pdf', out_name='../data/Endesa.jpg')`

### In case of Anaconda ###
    
    ImageMagick
    `$  http://docs.wand-py.org/en/latest/guide/install.html#install-imagemagick-on-windows`
     only latest version 6x work ImageMagick-6.9.8-9-Q16-x64-dll.exe
    
    PyPDF2
    `$  conda install -c conda-forge pypdf2`
        
    [pywand 0.44](https://github.com/dahlia/wand.git)
    `$  pip install wand`        
  
    [GhostScript](https://www.ghostscript.com/download/gsdnld.html)
        install with gs921w64.exe
                
    PythonMagic
		$pip install PythonMagick-0.9.13-cp35-cp35m-win_amd64.whl	
		http://support.cs.nott.ac.uk/help/docs/image/ImageMagick/www/windows.html	             
        
    [fpdf](http://code.google.com/p/pyfpdf)
        
    convert pdf to images

    call the google cloud vision api

