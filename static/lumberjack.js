// The main site is powered, rather unnecessarily, entirely by AJAX calls.

// Constants
var irc_refresh_in_seconds = 60;// How often we refresh the page
var page_hash_check_in_seconds = 1;// How often we check the page hash for changes.

// Globals (the horror)
var last_id = 0;// The ID of the comment at the very bottom of the page
var first_id = 0;// The ID of the comment at the very top of the page
var refresh_on = true;// Whether or not the 'refresh' action is currently operating
var hash = "#";// The most recent hash value in the URL ("#search-poop")

var current_offset = 50; // The current search offset;
var most_recent_search = ""; //The last thing searched for. 
var channel = null; // the channel being served

// On Load
$(function() {

  // set the channel
  channel = getParam("channel");
  if (channel && channel[0] != '#') channel = '#' + channel;
  
  // check for new content every N seconds
  
  setInterval("refresh()", irc_refresh_in_seconds * 1000);
  setInterval("hashnav_check()", page_hash_check_in_seconds * 1000);
    
  if( ! hashnav() ) { home(); }

  //Toolbar setup
  $("#load_more").click( load_more_search_results );
  $("#search").submit( search );
  $("#home").click( home );
  $("#prev").click( page_up );
  $("#next").click( page_down );
  $("#events").click( events );
  $("#important").click( important );

  $("#searchoptions").hide();
});


// getParam from http://ziemecki.net/content/javascript-parsing-url-parameters
function getParam ( sname )
{
  var params = window.location.search.substr(location.search.indexOf("?")+1);
  var sval = "";
  params = params.split("&");
    // split param and value into individual pieces
    for (var i=0; i<params.length; i++)
       {
         temp = params[i].split("=");
         if ( [temp[0]] == sname ) { sval = temp[1]; }
       }
  return sval;
}
// Navigate around the site based on the site hash.
// This allows for use of the "Back" button, as well as reusable URL structure. 
function hashnav()
{
  hash = window.location.hash
  if( hash.substring(1, 7) == "search")
  {
    var searchterm = hash.substring( 8, hash.length );
    $("#searchbox").attr({"value":searchterm});
    search();
    return true;
  }
  if( hash.substring(1, 4) == "tag")
  {
    var tagname = hash.substring( 5, hash.length );
    tag( tagname );
    return true;
  }
  else if (hash.substring(1, 3) == "id") 
  {
    var id = hash.substring( 4, hash.length );
    context(id);
    return true;
  }
  else if (hash.substring(1, 5) == "home") 
  {
    home();
    return true;
  }
  else if (hash.substring(1, 8) == "loading") 
  {
    return true;
  }
  return false;
}

// Check the current hash against the hash in the url. If they're different, perform hashnav.
// Note: this happens frequently
function hashnav_check()
{
  if( hash == window.location.hash )
  {
    return false;
  }
  else
  {
    return hashnav();
  }
}


// Populate the page with the last 50 things said
// This is the default 'home' activity for the page.
function home()
{
  clear();
  refresh_on = true;
  $('#irc').removeClass("searchresult");
  $("#options").show();
  $("#searchoptions").hide();
  // Ajax call to populate table
  loading()
  $.getJSON("json", { 'channel': channel},
  function(data){
    if (! data || ! data.length ){
        done_loading();
        return;
    }
    console.log(data);
    first_id = data[0].id;
    $(data).each( function(i, item) { 
      $("#irc").append(irc_render(item));
      last_id = item.id;
    });
    scroll_to_bottom();
    done_loading();
    window.location.hash = "home";
    hash = window.location.hash;
  });
}

// Check if anything 'new' has been said in the past minute or so. 
function refresh()
{
  if( !refresh_on ) { return; }
  loading();
  $.getJSON("json", { 'type':'update', 'id': last_id, 'channel': channel },
  function(data){
    $(data).each( function(i, item) { 
      try
      {
        $("#irc").append(irc_render(item));
        last_id = item.id; 
      }
      catch(err)
      {
        console.log(err);
      }
        
    });
    done_loading();
  });
}

// Perform a search for the given search value. Populate the page with the results.
function search_for( searchvalue )
{
  current_offset = 50;
  most_recent_search = searchvalue;
  window.location.hash = "search-"+searchvalue;
  hash = window.location.hash;
    
  //Before
  refresh_on = false;
  $("#options").hide();
  $("#searchoptions").show();

  clear();
  loading();

  // Ajax call to get search results
  $.getJSON("json", {'search':searchvalue, 'channel': channel},
  function(data){
    if( data.length < 50 ) { $("#searchoptions").hide(); }
    $(data).each( function(i, item) { try
      {
        $("#irc").append(irc_render(item));
      }
      catch(err)
      {
        console.log(err);
      }
    } );
    $("#irc").addClass("searchresult");
    done_loading(); 
    scroll_to_bottom();
        
  });
}

// Perform a search for the search value in the #searchbox element. 
function search()
{
  var searchvalue = escape($("#searchbox").attr("value"));
  search_for( searchvalue );
  return false; // This should prevent the search form from submitting
}

// Switch to a specific IRC message, centered about its ID.
function context(id)
{
  // Before
  clear();
  refresh_on = false;
  $("#options").show();
  $("#searchoptions").hide();

  $('#irc').removeClass("searchresult");
  loading();

  // Ajax call to get 'context' (find the comment at id 'id' and 'n' spaces around it). 
  $.getJSON("json", {'type':'context', 'id':id, 'channel': channel },
  function(data){
    if (! data || ! data.length ){
        done_loading();
        return;
    }
    first_id = data[0].id;
    $(data).each( function(i, item) { 
      $("#irc").append(irc_render(item)); 
      last_id = item.id; 
    });
        
    // After
    scroll_to_id( id );
    $('#irc-'+id).animate({fontSize: "150%"}, 2500);
    done_loading();
    window.location.hash = "id-"+id;
    hash = window.location.hash;
  });
    
}

/// add a pagebreak
function add_page_break(prepend) {
    var tr = $("<tr/>").addClass("pagebreak").append(
        $("<td/>").addClass("name")
    ).append(
        $("<td/>").addClass("message").html("------------------------------")
    ).append(
        $("<td/>").addClass("date")
    );
    if (prepend) {
        $("#irc").prepend(tr);
    } else {
        $("#irc").append(tr);
    }
    
}

// Add n more search results
function load_more_search_results()
{
  if( current_offset < 50 ){ current_offset = 50 };

  // Ajax call
  loading();
  $.getJSON("json", {'type':'search', 'n':50, 'offset':current_offset, 'search':most_recent_search, 'channel': channel },
  function(data){
    add_page_break(true);
    // $("<tr class='pagebreak'><td></td> <td>------------------------------</td> <td></td></tr>").prependTo("#irc");
    var id = 0;
    if( data.length < 50 ) { $("#searchoptions").hide(); }
    data.reverse();
    $(data).each( function( i, item) {
      $("#irc").prepend(irc_render(item));
      id = item.id;
    });
    scroll_to_id( id );
    done_loading();
    current_offset += 50;
  });
  return false;
}

// Add a page of IRC chat _before_ the current page of IRC chat
function page_up()
{
  // Ajax call to populate table
  loading();
  $.getJSON("json", {'type':'context', 'id':first_id, 'n':20, 'context':'before', 'channel': channel },
  function(data){
    add_page_break(true);
      
    // $("<tr class='pagebreak'><td></td> <td>------------------------------</td> <td></td></tr>").prependTo("#irc");
    $(data).each( function(i, item) { 
      $("#irc").prepend(irc_render(item)); 
      first_id = item.id; 
    });
    scroll_to_id( first_id );
    done_loading();
  });
  return false;   
}

// Add a page of IRC chat _after_ the current page of IRC chat
function page_down()
{
  loading();

  $.getJSON("json", {'type':'context', 'id':last_id, 'n':20, 'context':'after', 'channel': channel },
  function(data){
    add_page_break(false);
    // $("<tr class='pagebreak'><td></td> <td>------------------------------</td> <td></td></tr>").appendTo("#irc");
    $(data).each( function(i, item) { 
      $("#irc").append(irc_render(item)); 
      last_id = item.id; 
    });
        
    scroll_to_bottom();
    done_loading();
  });
  return false;
}

function events ( )
{
  tag( "event" );
  return false;
}

function important( )
{
  tag( "important" );
  return false;
}

// Load a tag
function tag( tagname ) 
{
  window.location.hash = "tag-"+tagname;
  hash = window.location.hash;

  clear();
  refresh_on = false;
  $("#options").hide();
  $("#searchoptions").hide();
  $('#irc').removeClass("searchresult");

  loading();
  $.getJSON("json", {'type':'tag', 'tag':tagname, 'n':15, 'channel': channel },
  function(data){
    $(data).each( function(i, item) { 
      $("#irc").append(irc_render(item));
    });
        
    done_loading();
    scroll_to_bottom();
  });
  return false;
}


//-----------------------------------------------

// Convert a single IRC message into a table row
function irc_render( item ) 
{
  if ( item.hidden != "F" ) { return "";} 

  var message_tag = /^\s*([A-Za-z]*):/.exec(item.message);
  var tag_tag = "";
  if (message_tag) 
  {
    message_tag = message_tag[1].toLowerCase();
    tag_tag = "tag";
  }
  else
  {
    message_tag = "";
  }
  var row = $("<tr/>");
  row.attr("id", "irc-" + item.id)
  row.addClass(item.type);
  row.addClass(message_tag);
  row.addClass(tag_tag);
  row.append(
    $("<td/>").addClass('name').append(
      $('<a/>').attr("href", "#id-" + item.id).html(item.name)
    )
  );
  var msg_td = $("<td/>").addClass('message');

  var construct_string = "";

  if (item.type == "pubmsg") { construct_string += ":&nbsp;";}
  else if (item.type == "join") { construct_string += "has joined " + html_escape(item.channel); }
  else if (item.type == "part") { construct_string += "has left " + html_escape(item.channel) + " -- "; }
  else if (item.type == "topic") { construct_string += "has changed the topic: <br/>"; } 
  else if (item.type == "nick") { construct_string += "is now known as ";}
  else if (item.type == "action") { }

  construct_string += link_replace(html_escape(item.message));
  msg_td.html(construct_string);
  row.append(
    msg_td
  );
  var message_date = datetimeify(item.time);
  row.append(
    $("<td/>").addClass('date').html(human_date(message_date))
  );
  return row;
}

// Make links clickable, and images images
function link_replace( string )
{
  links = string.match( /(http:&#x2F;&#x2F;\S*)/g  );
  if (links)
  {
    for( var i = 0; i < links.length; i++ )
    {
      var replacement = links[i]
      if (replacement.length > 100)
      {
        replacement = links[i].substring(0,100) + "...";
      }

      string = string.replace( links[i], "<a href='"+links[i]+"'>"+replacement+"</a>");
    }
  }
  return string;
}

// Show the 'loading' widget. 
function loading()
{
  $("#loading").show('fast');
  document.body.style.cursor = 'wait';
}

function done_loading()
{
  $('#loading').hide('slow');
  document.body.style.cursor = 'default';
}

// Clears the IRC area.
function clear()
{
  console.log("clear");
  $("#irc").html("");
}

// Scroll to the bottom of the page
function scroll_to_bottom()
{
  var target = $("#bottom");
  var targetOffset = target.offset().top;
  $('html,body').animate({scrollTop: targetOffset}, 1000);
}

// Attempt to scroll to the id of the item specified.
function scroll_to_id(id)
{
  var target = $("#irc-"+id);
  if (target.offset() === null) return;
  var targetOffset = target.offset().top - 100;
  $('html,body').animate({scrollTop: targetOffset}, 1000);
}

// MySQL date string (2009-06-13 18:10:59 / yyyy-mm-dd hh:mm:ss )
function datetimeify( mysql_date_string )
{
  var dt = new Date();
  var space_split = mysql_date_string.split(" ");
  var d = space_split[0];
  var t = space_split[1];
  var date_split = d.split("-");
  dt.setUTCFullYear( date_split[0] );
  dt.setUTCMonth( date_split[1]-1 );
  dt.setUTCDate( date_split[2] );
  var time_split = t.split(":");
  dt.setUTCHours( time_split[0] );
  dt.setUTCMinutes( time_split[1] );
  dt.setUTCSeconds( time_split[2] );
  return dt;
}

// human_date - tries to construct a human-readable date
function human_date( date )
{
  var td = new Date();
  var dt = date.toDateString()
  if( date.getDate() == td.getDate() && 
  date.getMonth() == td.getMonth() &&
  date.getYear() == td.getYear() ) { dt = "Today"; }

  var yesterday = new Date();
  yesterday.setDate( td.getDate() - 1 );

  if( date.getDate() == yesterday.getDate() && 
  date.getMonth() == yesterday.getMonth() &&
  date.getYear() == yesterday.getYear() ) { dt = "Yesterday";}

  if( hours == 0 && minutes == 0 ) { return dt + " - Midnight"; }
  else if( hours == 12 && minutes == 0 ){ return dt + " - Noon"; } 
  else
  {
    var ampm = "AM";
    var hours = date.getHours();
    if(hours > 11){ hours = hours - 12; ampm = "PM"; }

    var minutes = date.getMinutes();
    if( minutes < 10 ){ minutes = "0" + minutes; } 

    // I find it strange, but in a 12-hour clock, '12' acts as 0. 
    if( hours == 0 ) { hours = 12; }

    return dt + " - " + hours + ":" + minutes + " " + ampm;
  }
}

// Shouldn't this be part of javascript somewhere? 
// Nevetheless, escapes HTML control characters.
function html_escape( string )
{
  string = string.replace(/&/g, '&amp;');
  string = string.replace(/</g, '&lt;');
  string = string.replace(/>/g, '&gt;');
  string = string.replace(/\"/g, '&quot;' );
  string = string.replace(/'/g, '&#x27;' );
  string = string.replace(/\//g, '&#x2F;');
  return string;
}
