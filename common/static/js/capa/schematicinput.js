$(function() {
    // TODO: someone should fix all of this...
    //$("a[rel*=leanModal]").leanModal(); //TODO: Make this work with the new modal library. Try and integrate this with the "slices"

    $("body").append('\
    <div id="circuit_editor_modal" class="modal hide fade"> \
      <div class="modal-body"> \
        <input class="schematic" height="300" width="500" id="schematic_editor" name="schematic" type="hidden" value=""/> \
      </div> \
      <div class="modal-footer"> \
        <button type="button" id="circuit_save_btn" class="btn btn-primary" data-dismiss="modal"> \
          Save circuit \
        </button> \
      </div> \
    </div>');

    //This is the editor that pops up as a modal
    var editorCircuit = $("#schematic_editor").get(0);
    //This is the circuit that they last clicked. The one being edited.
    var editingCircuit = null;
    //Notice we use live, because new circuits can be inserted
    $(".schematic_open").live("click", function() {
      //Find the new editingCircuit. Transfer its contents to the editorCircuit
      editingCircuit = $(this).children("input.schematic").get(0);

      editingCircuit.schematic.update_value();
      var circuit_so_far = $(editingCircuit).val();

      var n = editorCircuit.schematic.components.length;
      for (var i = 0; i < n; i++)
        editorCircuit.schematic.components[n - 1 - i].remove();

      editorCircuit.schematic.load_schematic(circuit_so_far, "");
      editorCircuit.schematic.zoomall();
    });

    $("#circuit_save_btn").click(function () {
      //Take the circuit from the editor and put it back into editingCircuit
      editorCircuit.schematic.update_value();
      var saving_circuit = $(editorCircuit).val();

      var n = editingCircuit.schematic.components.length;
      for (var i = 0; i < n; i++)
        editingCircuit.schematic.components[n - 1 - i].remove();

      editingCircuit.schematic.load_schematic(saving_circuit, "");
      editingCircuit.schematic.zoomall();
    });
});
