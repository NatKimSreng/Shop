var $j = jQuery.noConflict();
$j(document).ready(function () {
  $j(document).on("click", "#add-cart", function (e) {
    e.preventDefault();

    var product_id = $j("#add-cart").val();
    var product_qty = $j("#qty-cart").val();

    if (!product_id || !product_qty || isNaN(product_qty) || product_qty < 1) {
      console.error("Invalid product ID or quantity", {
        product_id,
        product_qty,
      });
      alert("Please select a valid product and quantity.");
      return;
    }

    $j.ajax({
      type: "POST",
      url: '{% url "cart_add" %}',
      data: {
        product_id: product_id,
        product_qty: product_qty,
        csrfmiddlewaretoken: "{{ csrf_token }}",
        action: "post",
      },
      success: function (json) {
        document.getElementById("cart_quantity").textContent = json.qty;
        // Optionally update other UI elements or show a success message
        alert("Product added to cart!");
      },
      error: function (xhr, errmsg, err) {
        console.error(
          "Error:",
          xhr.responseJSON ? xhr.responseJSON.error : "Unknown error"
        );
        alert(
          "Failed to add to cart: " +
            (xhr.responseJSON ? xhr.responseJSON.error : "Unknown error")
        );
      },
    });
  });
});
