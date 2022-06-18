(function(){
  var FLAGS = {
    {% for flag, value in flags %}'{{ flag }}': {% if value %}true{% else %}false{% endif %}{% if not forloop.last %},{% endif %}{% endfor %}
    },
    SWITCHES = {
    {% for switch, value in switches %}'{{ switch }}': {% if value %}true{% else %}false{% endif %}{% if not forloop.last %},{% endif %}{% endfor %}
    },
    SAMPLES = {
    {% for sample, value in samples %}'{{ sample }}': {% if value %}true{% else %}false{% endif %}{% if not forloop.last %},{% endif %}{% endfor %}
    };
  window.waffle = {
    "flag_is_active": function waffle_flag(flag_name) {
      {% if flag_default %}
        if(FLAGS[flag_name] === undefined) return true;
      {% endif %}
      return !!FLAGS[flag_name];
    },
    "switch_is_active": function waffle_switch(switch_name) {
      {% if switch_default %}
        if(SWITCHES[switch_name] === undefined) return true;
      {% endif %}
      return !!SWITCHES[switch_name];
    },
    "sample_is_active": function waffle_sample(sample_name) {
      {% if sample_default %}
        if(SAMPLES[sample_name] === undefined) return true;
      {% endif %}
      return !!SAMPLES[sample_name];
    },
    "FLAGS": FLAGS,
    "SWITCHES": SWITCHES,
    "SAMPLES": SAMPLES
  };
})();
