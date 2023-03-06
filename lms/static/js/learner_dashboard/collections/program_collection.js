import Backbone from 'backbone';
import Program from '../models/program_model';

class ProgramCollection extends Backbone.Collection {
    constructor(models, options) {
        const defaults = {
            model: Program,
        };
        super(models, Object.assign({}, defaults, options));
    }
}

export default ProgramCollection;
