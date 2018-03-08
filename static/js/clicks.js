'use strict';

$('#challenge-form').on('click', showChallengeForm);
$('#shelf-button').on('click', function () {
    console.log('clicked!');
    showShelvesDiv();
});
$('#review-button').on('click', showReviewsDiv);
$('#shelf-select').on('click', showShelfSelect);

function showShelvesDiv(){
    $('#user-shelf-show').toggle("hidden2");
}

function showReviewsDiv(){
    $('#user-reviews').toggle("hidden2");
}

function showChallengeForm(){
    $('#create-challenge').toggle("hidden2");
}

function showShelfSelect() {
    $('#shelf-form').toggle("hidden2");
}