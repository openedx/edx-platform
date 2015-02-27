var studioSrc  = './cms/static',
    studioDest = './cms/static',
    lmsSrc     = './lms/static',
    lmsDest    = './lms/static';

module.exports = {
    styles: {
        lms: {
            src: lmsSrc + '/sass/**/*.scss',
            dest: lmsDest + '/css',
            clean: lmsDest + '/css/*.css'
        },

        studio: {
            src: studioSrc + '/sass/**/*.scss',
            dest: studioDest + '/css'
        }
    }
};
