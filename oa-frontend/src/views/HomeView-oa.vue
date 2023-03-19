<template>
  <div class="HomeView">
    <div class="messages">
      <div class="message" :class="{ bot: message.bot }" v-for="message in messages" v-html="message.message">
      </div>
    </div>
    <div class="footer">
      <div class="input-wrapper input">
        <contenteditable :placeholder="placeHolder" :class="{ empty: isInputEmpty, field: true }" tag="div"
          :contenteditable="true" v-model="message" :no-nl="false" :no-html="true" @keydown="handleKeyDown" />
        <button class="commit-button" v-if="!isInputEmpty" @click="clickSend">Send</button>
      </div>

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
      delimiter: '',
      inProgressMessage: '',
      inProgressMessageObject: {
        bot: true,
        message: ""
      },
      isTypingResult: false,
      typingInterval: -1,
      messageComplete: false
    }
  },
  computed: {
    isInputEmpty() {
      return this.message == '' || this.message == '\n'
    }
  },
  methods: {
    handleKeyDown(e) {
      if (e.keyCode == 13 && e.ctrlKey) {
        e.preventDefault();
        this.enterPressed();
      }
    },
    clickSend() {
      this.enterPressed();
    },
    enterPressed() {
      this.messages.push({
        bot: false,
        message: this.message
      })
      console.log(this.messages[0])
      //construct message to send to service
      var maxTurnsAsContext = 999;
      var messageStr = '';
      for (let index = this.messages.length - maxTurnsAsContext < 0 ? 0 : this.messages.length - maxTurnsAsContext; index < this.messages.length; index++) {
        const msg = this.messages[index];
        if (msg.bot) {
          messageStr += "<|assistant|>" + msg.message + "<|endoftext|>"
        }
        else {
          messageStr += "<|prompter|>" + msg.message + "<|endoftext|>"
        }
      }

      if (!this.messages.slice(-1).bot) {
        messageStr += "<|assistant|>"
      }
      // this.messages.forEach(msg => {
      //   if (msg.bot) {
      //     messageStr += 'Chip: ' + msg.message + this.delimiter
      //   }
      //   else {
      //     messageStr += 'User: ' + msg.message + this.delimiter
      //   }
      // });
      this.postData({ prompt: messageStr }).then((response) => {

        this.processResult(response)
      })

      this.message = '';
    },
    processResult(resultString) {
      // console.log(resultString)
      //check if it contains end of text token
      var endToken = "<|endoftext|>"
      var iterate = false;
      resultString = resultString.replaceAll("\n\n", "<br><br>");

      if (resultString.split(endToken).slice(-1) == "") {

        console.log('done')
        this.messageComplete = true;

      } else {
        iterate = true;
        this.messageComplete = false;
      }

      //process
      var messageArr = [];
      var messages = resultString.split("<|endoftext|>");
      for (let i = 0; i < messages.length; i++) {
        const msg = messages[i];
        if (msg != '') {
          if (msg.indexOf("<|prompter|>") > -1) {
            messageArr.push({
              bot: false,
              message: msg.split("<|prompter|>")[1]
            })
          } else {
            var msgObj = {
              bot: true,
              message: msg.replaceAll("<|assistant|>", "")
            }

            if (i == messages.length - 1) {
              this.inProgressMessage = msgObj.message;
              if (iterate) {
                messageArr.push(this.inProgressMessageObject)
                if (!this.isTypingResult) {
                  this.inProgressMessageObject.message = '';
                  this.startTypingResult();
                }
              } else {
                messageArr.push(msgObj)
              }
            }else{
              messageArr.push(msgObj)
            }

          }
        }
      }

      //assign it
      this.messages = messageArr;
      //iterate ?
      if (iterate) {
        this.postData({ prompt: resultString }).then((result) => {
          this.processResult(result)
        })
      }
    },
    startTypingResult() {
      this.isTypingResult = true;
      var charIndex = 0;
      this.typingInterval = setInterval(() => {
        if (this.messageComplete) {
          clearInterval(this.typingInterval);
          this.isTypingResult = false;
          console.log('done')
        }
        if (charIndex < this.inProgressMessage.length) {
          this.inProgressMessageObject.message += this.inProgressMessage.charAt(charIndex)
          charIndex++
        }
      }, 10);
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
      white-space: pre-line;
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
      display: flex;
      justify-content: space-between;
      background-color: #41414c;
      padding: 16px;
      border-radius: 6px;
      align-items: center;
    }

    .field {
      flex-grow: 1;
      min-height: 20px;

    }

    .field.empty:before {
      content: attr(placeholder);
      color: grey;
      font-style: italic;
      position: absolute;
    }
  }

  .commit-button {
    all: unset;
    background-color: rgba(0, 0, 0, .5);
    color: rgba(255, 255, 255, 1);
    border-radius: 4px;
    padding: 8px;
    font-size: 12px;
    align-self: flex-start;
    opacity: .6;
    cursor: pointer;
  }

  .commit-button:hover {
    opacity: 1;
  }

  .commit-button:active {
    opacity: .3;
  }

  [contenteditable]:focus {
    outline: 0px solid transparent;
  }
}
</style>