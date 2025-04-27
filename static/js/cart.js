document.addEventListener("DOMContentLoaded", function () {
  var updateBtns = document.getElementsByClassName("update-cart");
  console.log("Found buttons:", updateBtns.length);
  for (let i = 0; i < updateBtns.length; i++) {
    updateBtns[i].addEventListener("click", function () {
      var productId = this.dataset.product;
      var action = this.dataset.action;
      console.log("productId:", productId, "Action:", action);
    });
  }
});
