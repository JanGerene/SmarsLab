$('.control_button').on('click', function() {
  let controlId = $(this).attr('id');
  $.ajax({
    type: 'POST',
    url: '/controlapi',
    data: {
      "command": controlId
    },
    success: function() {
      // window.status = controlId

      console.log('POSTING: ' + controlId);
    },
    error: function() {
      // alert('error occured sending up command')
      console.log('error occured sending ' + controlId +' command');
    }
  })
});
