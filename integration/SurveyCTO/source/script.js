/* global fieldProperties, setAnswer, getPluginParameter, goToNextField, clearAnswer, setMetaData, getPluginParameter */

// Store current answer from fieldProperties
const current_answer = fieldProperties.CURRENT_ANSWER;

// Initialize dictionary that can store ultimate result.
const result_dict = {
    result: ''
};

/////////////////////////////////
// Required Plug-in Parameters //
/////////////////////////////////

const unique_profile_id = getPluginParameter("unique_profile_id");
const bace_url = getPluginParameter("bace_url");
const previous_choice = getPluginParameter("previous_choice");
const final_question = getPluginParameter("final_question") || 0; // Defaults to not being the final question.

/////////////////////////////////
// Optional Plug-in Parameters //
/////////////////////////////////

// DEFAULTS
var n_options_default = 2;
var split_to_rows_default = "|";
var split_to_vars_default = ":";
var buttons_per_row_default = 3;
var button_label_default = "Choice";
var profile_enumerator_default = "number"; // "number" or "letter". Defaults to "number"
var loading_message_default = "Your choice scenario is loading.\nWe appreciate your patience.";

// Assign Colors
var DARK_GREY = '#919492'
var LIGHT_GREY = '#dbdcdc'
var GREEN = '#4caf50'
var BLUE = '#008cba'
var RED = '#fe0000'

// Load in values
const split_to_rows = getPluginParameter("split_to_rows") || split_to_rows_default;
const split_to_vars = getPluginParameter("split_to_vars") || split_to_vars_default;
const n_options = getPluginParameter("n_options") || n_options_default;
const buttons_per_row = getPluginParameter("buttons_per_row") || buttons_per_row_default;
const button_label = getPluginParameter("button_label") || button_label_default;
const profile_enumerator = getPluginParameter("profile_enumerator") || profile_enumerator_default;
const loading_message = getPluginParameter("loading_message") || loading_message_default;

// Get answers parameters then store as array.
function answersArray(n) {
    let answers_arr = Array.from({length: n}, (_, i) => i);
    return answers_arr.join(',');
}

var answers_default = answersArray(n_options);
let answers_full = getPluginParameter("answers") || answers_default;

console.log('Answers array: ')
console.log(answers_full);

const answers = answers_full.split(',');
console.log('Answers:')
console.log(answers);

/////////////////////////////////
/////////// FUNCTIONS ///////////
/////////////////////////////////

function addAnswerButtons(n_options = n_options_default, buttons_per_row = buttons_per_row_default, button_label = button_label_default, profile_enumerator = profile_enumerator_default) {

    // Require at least two buttons
    if (!Number.isInteger(n_options) || n_options < 2) {
        n_options = 2;
      }

    // Get table with answers button and clear existing content.
    const table = document.getElementById('answerButtonsTable');
    table.innerHTML = '';
  
    let row = table.insertRow(); // Create a new row
  
    for (let i = 1; i <= n_options; i++) {
      const cell = row.insertCell(); // Create a new cell

      if (profile_enumerator === 'letter') {
          enumerator = String.fromCharCode(65 + i - 1); // Use letters for headers (A, B, C, ...)
      } else {
        enumerator = i; // Use numbers for headers (1, 2, 3, ...)
      }
  
      const button = document.createElement('button');
      button.id = `button${i}`;
      button.innerHTML = `${button_label} ${enumerator}`;
      button.className = 'button';

      button.onclick = function() { eval(`addResult(answer_index=${i - 1})`); }; // Assuming addResultX functions exist
  
      cell.appendChild(button);
  
      if (i % buttons_per_row === 0 && i !== n_options) {
        row = table.insertRow();
      }
    }
  }

function addResult(answer_index) {

    // Use result_dict to access results
    var result = result_dict['result'];
    var answer_to_store = result + answer_index;

    // Fix the button colors
    fixButtonColors(answer_index);
    setAnswer(answer_to_store);
}

// Function to fix button colors on click.
function fixButtonColors(answer_index, alreadyAnswered=false) {

    // Get all buttons  
    const buttons = document.querySelectorAll('#answerButtonsTable button');

    // Set Colors
    var selectedColor = (alreadyAnswered) ? DARK_GREY : GREEN;
    var unselectedColor = (alreadyAnswered) ? LIGHT_GREY : BLUE;

    buttons.forEach((button, i) => {
        button.style.backgroundColor = (i == answer_index) ? selectedColor : unselectedColor;
    })

}



// Function to create and display a table with dynamic headers based on the profile enumerator
function createTable(table_id, table_components, button_label=button_label_default, profile_enumerator = profile_enumerator_default) {

    // Split the input data into rows
    const rows = table_components.split(split_to_rows);
    // Create the table element
    const table = document.createElement('table');
    table.id = table_id;
    table.className = "bace_table";
  
    // Return if there are no rows to display
    if (rows.length === 0) {
      return;
    }
  
    // Determine the number of profiles (columns) based on the first row
    const firstRowValues = rows[0].split(split_to_vars);
    const numProfiles = firstRowValues.length;
  
    // Create the table header with the appropriate number of profile columns
    const headerRow = document.createElement('tr');
    headerRow.innerHTML += '<th></th>'; // Create an empty header cell for the first column
    
    // Loop through the number of profiles to create header cells
    for (let i = 1; i < numProfiles; i++) {
        let headerContent;

        if (profile_enumerator==null){

            headerRow.innerHTML += `<th>${button_label}</th>`;

        } else {
            if (profile_enumerator === 'letter'){
                headerContent = String.fromCharCode(65 + i - 1); // Use letters for headers (A, B, C, ...)
            } else {
                headerContent = i; // Use numbers for headers (1, 2, 3, ...)
            }
            headerRow.innerHTML += `<th>${button_label} ${headerContent}</th>`;
        }


    }

    // Append the header row to the table
    table.appendChild(headerRow);
  
    // Loop through each row of data
    for (const rowData of rows) {
        const rowValues = rowData.split(split_to_vars);
        const row = document.createElement('tr');

        // Check if each row is empty and has the correct number of columns
        if (rowValues.length !== numProfiles) {
            console.error(`Row does not have expected number of columns.\nRow Data: ${rowData}`);
            continue; // Skip rows with incorrect number of columns
        }

        // Create cells for each value in the row
        for (const value of rowValues) {
            const cell = document.createElement('td');
            cell.innerHTML = value;
            row.appendChild(cell);
        }

        // Append the row to the table
        table.appendChild(row);
    }
  
    // Append the completed table to the container
    var bace_container = document.getElementById('bace_container');
    bace_container.appendChild(table);
}

// Function to change button status
function disableButtons() {
    const buttons = document.querySelectorAll('#answerButtonsTable button'); // Get all buttons  
    buttons.forEach((button, i) => { button.disabled = true; })
}

function enableButtons() {
    const buttons = document.querySelectorAll('#answerButtonsTable button'); // Get all buttons  
    buttons.forEach((button, i) => { button.disabled = false; })
}


////////////////////////////////
///////// BACE QUERIES /////////
////////////////////////////////

// Queries API to (update answer history) and select new designs
// Should query the /surveyCTO route
function getNextDesign(bace_url, data, n_options, buttons_per_row, button_label, profile_enumerator) {

    console.log('calling getnextdesign');

    fetch(bace_url, {
        method: 'POST', // HTTP method: POST
        headers: header, // Add headers
        body: JSON.stringify(data) // Converting request body to JSON string.
    })
    .then((res) => res.json())
    .then((output) => {
        

        // Debugging Methods
        console.log('Message received');
        console.log(output);

        // Delete loading message
        deleteLoadingMessage();

        // Log design
        let design = output['output'];
        console.log(design);

        result_dict['result'] = design;

        // Add answer buttons and disable them.
        addAnswerButtons(n_options, buttons_per_row, button_label, profile_enumerator);
        disableButtons();
        
        // Create table
        createTable('bace_table', design, button_label, profile_enumerator);
    })
    .then(() => {
        enableButtons();
    })
    .catch(error => console.error('Error:', error)); // Adding error handling

}

// Function to send after final question to update profile and store estimates.
function getEstimates(bace_url, data) {

    fetch(bace_url, {
        method: 'POST', // HTTP method: POST
        headers: header, 
        body: JSON.stringify(data)
    })
    .then((res) => res.json())
    .then((estimates) => {

        deleteLoadingMessage();

        let posterior_estimates = estimates['estimates'];
        console.log(posterior_estimates);
        result_dict['result'] = posterior_estimates;

        createTable('bace_table', posterior_estimates, "Estimates", null);
        setAnswer(posterior_estimates);
    })
    .catch(error => console.error('Error:', error)); // Adding error handling

}



// Function to query the API for a random design.
function getRandomDesign(bace_url) {

    fetch(bace_url)
        .then((res) => res.json())
        .then((output) => {

            let design = output['output']
            console.log(design)
            result_dict['result'] = design;

            addAnswerButtons(n_options, buttons_per_row, button_label, profile_enumerator);
            disableButtons();
    
            createTable('bace_table', design, button_label, profile_enumerator);
        })
        .then(() => enableButtons())
        .then(() => deleteLoadingMessage())
        .catch(error => console.error('Error:', error));
}

// Functions to Add/Delete the loading symbol
const loadingSymbolDivId = "loadingSymbolDiv";

function addLoadingMessage(message=loading_message, id=loadingSymbolDivId){

    var loadingDiv = document.getElementById(loadingSymbolDivId);
    loadingDiv.innerHTML = message + "<div class='loading-symbol'></div>"

}

function deleteLoadingMessage(id=loadingSymbolDivId) {
    //document.getElementById(id).style.display = 'none';
    document.getElementById('loadingScreen').style.display = 'none';
    document.getElementById('mainContent').style.display = 'block';
}

////////////////////////////////////////////
/////         Application Logic        /////
////////////////////////////////////////////

// Check if current answer already exists.
var already_answered = current_answer != null;

var this_profile_enumerator = (!final_question) ? profile_enumerator : null;
var this_button_label = (!final_question) ? button_label : "Estimates";

// Headers for HTML request
const header = { 
    'Accept': 'application/json', 
    'Content-Type': 'application/json' 
};

// Basic Request data
var request_data = {
    profile_id: unique_profile_id,
    return_estimates: (final_question) ? 1 : 0
}

// If first question and add_to_profile_vars is not empty. Add variables to request data
let add_to_request_vars = getPluginParameter("add_to_request_vars");
console.log('Add to request');
console.log(add_to_request_vars);
if (add_to_request_vars){
    const request_var_keys = add_to_request_vars.split(',');

    request_var_keys.forEach(k => {
        request_data[k] = getPluginParameter(k);
    })
}

console.log('request data');
console.log(request_data);

console.log('previous_choice');
console.log(previous_choice)

if (previous_choice != ""){
    request_data['answer'] = answers[previous_choice];
}


if (already_answered) {

    console.log('Already answered. Creating from previous.')

    // Render table from previous answer.
    createTable("bace_table", current_answer, this_button_label, this_profile_enumerator);
    deleteLoadingMessage();

    // Add answer choices 
    if (!final_question){

        console.log('Not final question. Adding answer buttons.');

        // Get previous answer choice. (Final element after splitting by `split_to_rows`)
        var answer_split = current_answer.split(split_to_rows);
        var selected_answer_index = answer_split[answer_split.length - 1];

        // Add answer buttons and disable them.
        addAnswerButtons(n_options, buttons_per_row, button_label, profile_enumerator);
        disableButtons();

        // Fix button colors;
        fixButtonColors(selected_answer_index, already_answered);
        
    }

} 
else {

    console.log('New question. Displaying request_data...');
    console.log(request_data);

    if (!final_question){
        console.log('Getting next design.');
        getNextDesign(bace_url, request_data, n_options, buttons_per_row, this_button_label, this_profile_enumerator);
    } else {
        // Final questions. Update API and store estimates.
        console.log('Sending final answer and obtaining estimates.');
        getEstimates(bace_url, request_data);
    }

}

// window.addEventListener('beforeunload', function (e) {
//     // Cancel the event as stated by the standard.
//     e.preventDefault();
//     // Chrome requires returnValue to be set.
//     e.returnValue = 'Are you sure you want to leave? Data you have entered may be lost or saved incorrectly.';
//     // Some browsers may display a default message instead of the custom message above.
// });
