<template>
  <div class="HomeView">
    <div class="messages">
      <div class="message" :class="{ bot: message.bot }" v-for="message in messages">{{ message.message }}
      </div>
    </div>
    <div class="footer">
      <contenteditable class="input" :placeholder="placeHolder" :class="{ empty: isInputEmpty }" tag="div"
        :contenteditable="true" v-model="message" :no-nl="false" :no-html="true" @keydown="handleKeyDown" />
    </div>

  </div>
</template>

<script>
import contenteditable from 'vue-contenteditable'

export default {
  components: {
    contenteditable
  },
  data() {
    return {
      // key: value
      messages: [],
      placeHolder: 'Type your message',
      message: '',
      lastRawResponse: '',
      delimiter: '\n\n\n'
    }
  },
  computed: {
    isInputEmpty() {
      return this.message == '' || this.message == '\n'
    }
  },
  methods: {
    handleKeyDown(e){
      if(e.keyCode == 13 && e.ctrlKey){
        e.preventDefault();
        this.enterPressed();
      }
    },
    enterPressed() {
      this.messages.push({
        bot: false,
        message: this.message
      })
      //construct message to send to service
      var maxTurnsAsContext = 10;
      var messageStr = '';
      for (let index = this.messages.length - maxTurnsAsContext < 0? 0 : this.messages.length - maxTurnsAsContext; index < this.messages.length; index++) {
        const msg = this.messages[index];
        if (msg.bot) {
          messageStr += 'Chip: ' + msg.message + this.delimiter
        }
        else {
          messageStr += 'User: ' + msg.message + this.delimiter
        }
      }
      // this.messages.forEach(msg => {
      //   if (msg.bot) {
      //     messageStr += 'Chip: ' + msg.message + this.delimiter
      //   }
      //   else {
      //     messageStr += 'User: ' + msg.message + this.delimiter
      //   }
      // });
      this.postData({ prompt: messageStr + "Chip:" }).then((response) => {
        this.processResult(response)
      })

      this.message = '';
    },
    processResult(resultString) {
      //check if it contains end of text token
      var endToken = "<|endoftext|>"
      var iterate = false;
      if (resultString.indexOf(endToken) > -1) {
        //strip it
        resultString = resultString.replaceAll(endToken, "");
        // resultString = resultString.replaceAll("\n\n\n\n\n", "");
        console.log('done')
      } else {
        iterate = true;
      }
      //process
      var messageArr = [];
      var messages = resultString.split(this.delimiter);
      messages.forEach(msg => {
        if (msg.split("User: ").length > 1) {
          messageArr.push({
            bot: false,
            message: msg.split("User: ")[1]
          })
        }
        if (msg.split("Chip: ").length > 1) {
          messageArr.push({
            bot: true,
            message: msg.split("Chip: ")[1]
          })
        }
      });
      //assign it
      this.messages = messageArr;
      //iterate ?
      if(iterate){
        this.postData({ prompt: resultString }).then((result) => {
          this.processResult(result)
        })
      }
    },
    async postData(prompt) {

      const response = await fetch('http://192.168.0.140:8000/generate', {
        method: 'POST',
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(prompt)
      })
      const json = await response.json();
      return json
    }
  },
  mounted() {

  },
}
</script>

<style lang="less" scoped>
.HomeView {

  box-sizing: border-box;
  overflow: auto;
  display: flex;
  flex-direction: column;
  height: 100%;

  .messages {
    display: flex;
    flex-direction: column;
    row-gap: 16px;
    box-sizing: border-box;
    flex-grow: 1;
    overflow: auto;

    .message {
      box-sizing: border-box;
      padding: 16px;

    }

    .bot {
      background-color: #444655;
    }
  }



  .footer {
    padding: 16px;

    width: 100%;
    box-sizing: border-box;

    .input {
      background-color: #41414c;
      padding: 16px;
      border-radius: 6px;
    }

    .input.empty:before {
      content: attr(placeholder);
      color: grey;
      font-style: italic;
      position: absolute;
    }
  }

  [contenteditable]:focus {
    outline: 0px solid transparent;
  }
}
</style>