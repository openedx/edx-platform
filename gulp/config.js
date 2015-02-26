var studioSrc  = './cms/static',
    studioDest = './cms/static',
    lmsSrc     = './lms/static',
    lmsDest    = './lms/static';

module.exports = {
    stylesStudio: {
        src: studioSrc + '/sass/**/*.scss',
        dest: studioDest + '/css'
    }
};
