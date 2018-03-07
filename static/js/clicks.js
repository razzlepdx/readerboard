'use strict';

$('#challenge-form').on('click', showChallengeForm);
$('#shelf-button').on('click', showShelvesDiv);
$('#review-button').on('click', showReviewsDiv);


function showShelvesDiv(){
    $('#user-shelves').toggle("hidden2");
}

function showReviewsDiv(){
    $('#user-reviews').toggle("hidden2");
}

function showChallengeForm(){
    $('#create-challenge').toggle("hidden2");
}