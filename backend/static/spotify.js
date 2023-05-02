// Set up the OAuth configuration
const CLIENT_ID = '62df10fd27b24fe3bbf1256444216cd0';
const CLIENT_SECRET = "b629c5fdb5434143acc97b73d18b7100";
const REDIRECT_URI = 'http://localhost:5000';
const SCOPE = 'playlist-modify-private playlist-modify-public';
var AUTH_URL = 'https://accounts.spotify.com/authorize' +
  '?response_type=token' +
  '&client_id=' + encodeURIComponent(CLIENT_ID) +
  '&scope=' + encodeURIComponent(SCOPE) +
  '&redirect_uri=' + encodeURIComponent(REDIRECT_URI);


var playlistGenerated = false;
var playlistId = '';
var playlistURI = '';
// Get the access token and expiration time from the URL fragment
var hashParams = window.location.hash.substr(1)
  .split('&')
  .reduce(function (result, item) {
    var parts = item.split('=');
    result[parts[0]] = parts[1];
    return result;
  }, {});

var access_token = hashParams.access_token;
var expires_at = hashParams.expires_in ? (new Date().getTime() + hashParams.expires_in * 1000) : null;

if (!access_token || (expires_at && expires_at < new Date().getTime())) {
  // The access token is missing or has expired
  // The user has not yet authorized the app - redirect to the Spotify authorization page
  window.location = AUTH_URL;

} else {
  // The user has authorized the app - use the access token to make a request to the Spotify Web API
  var test = fetch('https://api.spotify.com/v1/me', {
    headers: {
      'Authorization': 'Bearer ' + access_token
    }
  })
    .then(response => response.json())
    .then(data => {
      const createPlaylistEndpoint = `https://api.spotify.com/v1/users/${data.id}/playlists`;
      const createPlaylistOptions = {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${access_token}`
        },
        body: JSON.stringify({
          name: 'My Awesome Playlist',
          description: 'test playlist',
          public: false
        })
      };

      // Use the existing access token to make authorized requests to the Spotify Web API

      fetch(createPlaylistEndpoint, createPlaylistOptions)
        .then(response => response.json())
        .then(data => {
          // The playlist has been created successfully
          console.log('Playlist created:', data);
          playlistId = data.id;
          playlistURI = data.uri;
        })
        .catch(error => {
          // An error occurred while creating the playlist
          console.error('Error creating playlist:', error);
        });
    })
    .catch(error => {
      console.error('Error:', error);
      if (error.status === "401") {
        window.location = AUTH_URL;
      }
    });
}

async function searchTrack(trackName, artistName, accessToken) {
  // Encode the search query parameters
  const query = encodeURIComponent(`track:${trackName} artist:${artistName}`);

  // Send a request to the Spotify Web API search endpoint
  const response = await fetch(`https://api.spotify.com/v1/search?type=track&q=${query}`, {
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  });

  // Parse the response as JSON
  const data = await response.json();
  // Extract the first track from the response (if any)
  const track = await data.tracks.items[0];
  if (track != null) {
    return track.uri;
  } else {
    return '';
  }
}

function addTrackToPlaylist(trackURI) {
  // If there's no access token, redirect the user to the Spotify authorization page
  if (!access_token) {
    window.location = AUTH_URL;
    return;
  }

  // Get the user's display name
  return fetch('https://api.spotify.com/v1/me', {
    headers: {
      'Authorization': 'Bearer ' + access_token
    }
  })
    .then(response => response.json())
    .then(data => {
      // Add the track to the "My Awesome Playlist"
      return fetch(`https://api.spotify.com/v1/users/${data.id}/playlists/${playlistId}/tracks?uris=${encodeURIComponent(trackURI)}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${access_token}`
        }
      })
        .then(response => response.json())
        .then(data => {
          console.log(`Track ${trackURI} added to playlist`);
        })
        .catch(error => {
          console.error('Error adding track to playlist:', error);
        });
    })
    .catch(error => {
      console.error('Error:', error);
    });
}

function getAccessToken() {
  return access_token;
}
// async function getPlaylistId() {
//   if (playlistGenerated) {
//     return playlistId;
//   } else {
//     return 0;
//   }
// }

async function generatePlaylistEmbed() {
  // const embedUrl = `https://open.spotify.com/oembed?url=${playlistURI}&format=json`;

  // fetch(embedUrl)
  //   .then(response => response.json())
  //   .then(data => {
  //     // Handle the oEmbed data
  //     const iframe = document.createElement('div');
  //     iframe.innerHTML = data.html;
  //     iframe.setAttribute('class', 'spotify_embed');
  //     document.getElementById("answer-box").appendChild(iframe);
  //   })
  //   .catch(error => {
  //     console.error('Error generating playlist embed:', error);
  //   });
  const embedUrl = `https://open.spotify.com/oembed?url=${playlistURI}&format=json`;

  try {
    const response = await fetch(embedUrl);
    if (!response.ok) {
      throw new Error(`Failed to fetch embed data: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();

    // Handle the oEmbed data
    const iframe = document.createElement('div');
    iframe.innerHTML = data.html;
    iframe.setAttribute('class', 'spotify_embed');
    document.getElementById("answer-box").appendChild(iframe);
    console.log(iframe);
  } catch (error) {
    console.error('Error generating playlist embed:', error);
  }
}