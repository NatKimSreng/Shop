const cartUpdateUrl = "{% url 'cart_update' %}";
const cartDeleteUrl = "{% url 'cart_delete' %}";
const csrfToken = "{{ csrf_token }}";
var $j = jQuery.noConflict();
$j(document).ready(function () {
  // Add to Cart (product listing and detail pages)
  $j(document).on("click", ".add-cart", function (e) {
    e.preventDefault();
    var $button = $j(this);
    var product_id = $button.val();
    var product_qty = $j("#qty-cart").length ? $j("#qty-cart").val() : 1;

    if (!product_id || !product_qty || isNaN(product_qty) || product_qty < 1) {
      console.error("Invalid product ID or quantity", {
        product_id,
        product_qty,
      });
      alert("Please select a valid product and quantity.");
      return;
    }

    $button.prop("disabled", true).text("Adding...");
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
        $button.prop("disabled", false).text("Add to Cart");
        if (document.getElementById("cart_quantity")) {
          document.getElementById("cart_quantity").textContent = json.qty;
        }
        alert("Product added to cart!");
      },
      error: function (xhr, errmsg, err) {
        $button.prop("disabled", false).text("Add to Cart");
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
  $j(document).on("click", ".delete-cart", function (e) {
    e.preventDefault();
    const $button = $j(this);
    const product_id = $button.data("product-id");
    const action = $button.data("action");

    if (!product_id || !action) {
      console.error("Missing product_id or action");
      alert("Invalid product or action.");
      return;
    }

    $button.addClass("loading").prop("disabled", true);

    $j.ajax({
      type: "POST",
      url: "{% url 'cart_delete' %}",
      headers: { "X-CSRFToken": "{{ csrf_token }}" },
      data: {
        product_id: product_id,
        action: action,
      },
      dataType: "json",
      success: function (json) {
        $button.removeClass("loading").prop("disabled", false);
        if (!json.success) {
          alert(json.error || "An error occurred.");
          return;
        }
        location.reload();
      },

      error: function (xhr) {
        $button.removeClass("loading").prop("disabled", false);
        const errorMsg =
          xhr.responseJSON?.error || "An error occurred. Please try again.";
        console.error("Error:", errorMsg);
        alert(errorMsg);
      },
    });
  });
  // Update Cart (cart summary page)
  $j(document).on("click", ".update-cart", function (e) {
    e.preventDefault();
    var $button = $j(this);
    var product_id = $button.data("product-id");
    var action = $button.data("action");

    $button.prop("disabled", true);
    $j.ajax({
      type: "POST",
      url: '{% url "cart_update" %}',
      data: {
        product_id: product_id,
        action_type: action,
        csrfmiddlewaretoken: "{{ csrf_token }}",
        action: "post",
      },
      success: function (json) {
        $button.prop("disabled", false);
        if (document.getElementById("cart_quantity")) {
          document.getElementById("cart_quantity").textContent = json.qty;
        }
        // Update item quantity and total in the DOM
        $button.closest(".cart-row").find(".quantity").text(json.item_quantity);
        $button
          .closest(".cart-row")
          .find("div:last p")
          .text("$" + json.cart_total.toFixed(2));
        // Update cart total in the table
        $j("table .table h5 strong:last").text(
          "$" + json.cart_total.toFixed(2)
        );
        // Remove row if quantity is 0
        if (json.item_quantity <= 0) {
          $button.closest(".cart-row").remove();
        }
        location.reload();
      },
      error: function (xhr, errmsg, err) {
        $button.prop("disabled", false);
        console.error(
          "Error:",
          xhr.responseJSON ? xhr.responseJSON.error : "Unknown error"
        );
        alert(
          "Failed to update cart: " +
            (xhr.responseJSON ? xhr.responseJSON.error : "Unknown error")
        );
      },
    });
  });
});
